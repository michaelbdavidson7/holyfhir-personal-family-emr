use std::{
    env,
    fs::{self, OpenOptions},
    io::Write,
    net::TcpStream,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::Mutex,
    thread,
    time::{Duration, Instant},
};

use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

const HOST: &str = "127.0.0.1";
const PORT: u16 = 8787;
#[cfg(target_os = "windows")]
const CREATE_NO_WINDOW: u32 = 0x08000000;

struct DjangoProcess(Mutex<Option<Child>>);

#[derive(Clone)]
struct RuntimePaths {
    project_root: PathBuf,
    app_data_dir: PathBuf,
    env_file: PathBuf,
    env_example_file: PathBuf,
    database_file: PathBuf,
    log_file: PathBuf,
}

fn project_root(app: &tauri::AppHandle) -> PathBuf {
    if cfg!(debug_assertions) {
        env::current_dir().expect("failed to read current working directory")
    } else {
        let resource_dir = app
            .path()
            .resource_dir()
            .expect("failed to find bundled resources directory");

        [
            resource_dir.clone(),
            resource_dir.join("_up_"),
            installed_app_dir()
                .map(|path| path.join("_up_"))
                .unwrap_or_else(|_| resource_dir.join("_up_")),
        ]
        .into_iter()
        .find(|path| path.join(".env.example").exists() && path.join("manage.py").exists())
        .unwrap_or(resource_dir)
    }
}

fn installed_app_dir() -> Result<PathBuf, String> {
    env::current_exe()
        .map_err(|error| format!("failed to find current executable path: {error}"))?
        .parent()
        .map(Path::to_path_buf)
        .ok_or_else(|| "failed to find current executable directory".to_string())
}

fn early_log(message: impl AsRef<str>) {
    let Ok(app_dir) = installed_app_dir() else {
        return;
    };

    let log_file = app_dir.join("holyfhir-desktop.log");

    if let Ok(mut file) = OpenOptions::new().create(true).append(true).open(log_file) {
        let _ = writeln!(file, "{}", message.as_ref());
    }
}

fn runtime_paths(app: &tauri::AppHandle) -> Result<RuntimePaths, String> {
    let project_root = project_root(app);
    let app_data_dir = if let Ok(data_dir) = env::var("HOLYFHIR_DATA_DIR") {
        PathBuf::from(data_dir)
    } else if cfg!(debug_assertions) {
        project_root.join(".desktop-data")
    } else {
        installed_app_dir()?
    };

    fs::create_dir_all(&app_data_dir)
        .map_err(|error| format!("failed to create app data directory {app_data_dir:?}: {error}"))?;

    Ok(RuntimePaths {
        env_file: app_data_dir.join(".env"),
        env_example_file: project_root.join(".env.example"),
        database_file: app_data_dir.join("holyfhir.encrypted.sqlite3"),
        log_file: app_data_dir.join("holyfhir-desktop.log"),
        project_root,
        app_data_dir,
    })
}

fn python_executable() -> String {
    env::var("HOLYFHIR_PYTHON").unwrap_or_else(|_| "python".to_string())
}

fn append_log(paths: &RuntimePaths, message: impl AsRef<str>) {
    if let Ok(mut file) = OpenOptions::new()
        .create(true)
        .append(true)
        .open(&paths.log_file)
    {
        let _ = writeln!(file, "{}", message.as_ref());
    }
}

fn configure_django_command(command: &mut Command, paths: &RuntimePaths) {
    command
        .current_dir(&paths.project_root)
        .env("DJANGO_SETTINGS_MODULE", "config.settings")
        .env("DJANGO_ENV_FILE", &paths.env_file)
        .env("DJANGO_ENV_EXAMPLE_FILE", &paths.env_example_file)
        .env("DATABASE_NAME", &paths.database_file)
        .env("HOLYFHIR_BACKEND_LOG", &paths.log_file);
}

#[cfg(target_os = "windows")]
fn hide_backend_console(command: &mut Command) {
    use std::os::windows::process::CommandExt;

    command.creation_flags(CREATE_NO_WINDOW);
}

#[cfg(not(target_os = "windows"))]
fn hide_backend_console(_command: &mut Command) {}

fn bundled_backend_executable(paths: &RuntimePaths) -> PathBuf {
    let candidates = [
        paths
            .project_root
            .join("desktop-backend")
            .join("dist")
            .join("HolyFHIRBackend")
            .join("HolyFHIRBackend.exe"),
        paths
            .project_root
            .join("HolyFHIRBackend")
            .join("HolyFHIRBackend.exe"),
    ];

    candidates
        .iter()
        .find(|path| path.exists())
        .cloned()
        .unwrap_or_else(|| {
            paths
                .project_root
                .join("desktop-backend")
                .join("dist")
                .join("HolyFHIRBackend")
                .join("HolyFHIRBackend.exe")
        })
}

fn bundled_backend_candidates(paths: &RuntimePaths) -> String {
    [
        paths
            .project_root
            .join("desktop-backend")
            .join("dist")
            .join("HolyFHIRBackend")
            .join("HolyFHIRBackend.exe"),
        paths
        .project_root
        .join("HolyFHIRBackend")
            .join("HolyFHIRBackend.exe"),
    ]
    .iter()
    .map(|path| format!("{path:?}"))
    .collect::<Vec<_>>()
    .join(", ")
}

fn django_command(paths: &RuntimePaths) -> Result<Command, String> {
    let mut command = if cfg!(debug_assertions) {
        let mut command = Command::new(python_executable());
        command.arg("manage.py");
        command
    } else {
        let backend_executable = bundled_backend_executable(paths);

        if !backend_executable.exists() {
            return Err(format!(
                "missing bundled backend executable. Tried: {}",
                bundled_backend_candidates(paths)
            ));
        }

        let mut command = Command::new(backend_executable);
        command.arg("--project-root").arg(&paths.project_root);
        command
    };

    configure_django_command(&mut command, paths);
    hide_backend_console(&mut command);

    Ok(command)
}

fn command_output(command: &mut Command, paths: &RuntimePaths, label: &str) -> Result<(), String> {
    append_log(paths, format!("running {label}"));

    let output = command
        .output()
        .map_err(|error| format!("failed to run {label}: {error}"))?;

    append_log(
        paths,
        format!("{label} exited with status {}", output.status),
    );

    if !output.stdout.is_empty() {
        append_log(paths, String::from_utf8_lossy(&output.stdout));
    }

    if !output.stderr.is_empty() {
        append_log(paths, String::from_utf8_lossy(&output.stderr));
    }

    if output.status.success() {
        Ok(())
    } else {
        Err(format!("{label} failed with status {}", output.status))
    }
}

fn bootstrap_django(paths: &RuntimePaths) -> Result<(), String> {
    if !paths.env_example_file.exists() {
        return Err(format!(
            "missing bundled environment template: {:?}",
            paths.env_example_file
        ));
    }

    if !paths.env_file.exists() {
        let mut command = django_command(paths)?;
        command
            .arg("bootstrap_secrets")
            .arg("--env-file")
            .arg(&paths.env_file)
            .arg("--example-file")
            .arg(&paths.env_example_file)
            .arg("--yes");
        command_output(&mut command, paths, "bootstrap_secrets")?;
    }

    let mut command = django_command(paths)?;
    command.arg("migrate").arg("--noinput");
    command_output(&mut command, paths, "migrate")?;

    Ok(())
}

fn start_django(paths: &RuntimePaths) -> Result<Child, String> {
    let url = format!("{HOST}:{PORT}");
    let mut command = django_command(paths)?;

    command
        .arg("runserver")
        .arg(url)
        .arg("--noreload")
        .stdout(Stdio::null())
        .stderr(
            OpenOptions::new()
                .create(true)
                .append(true)
                .open(&paths.log_file)
                .map_err(|error| format!("failed to open log file {:?}: {error}", paths.log_file))?,
        )
        .spawn()
        .map_err(|error| format!("failed to start Django: {error}"))
}

fn wait_for_django() -> Result<(), String> {
    let deadline = Instant::now() + Duration::from_secs(20);

    while Instant::now() < deadline {
        if TcpStream::connect((HOST, PORT)).is_ok() {
            return Ok(());
        }

        thread::sleep(Duration::from_millis(250));
    }

    Err("Django did not start within 20 seconds".to_string())
}

fn is_django_running() -> bool {
    TcpStream::connect((HOST, PORT)).is_ok()
}

fn show_app_window(app: &mut tauri::App, url: WebviewUrl, title: &str) -> tauri::Result<()> {
    WebviewWindowBuilder::new(app, "main", url)
        .title(title)
        .inner_size(1280.0, 900.0)
        .min_inner_size(960.0, 640.0)
        .build()?;

    Ok(())
}

fn show_startup_error(app: &mut tauri::App, paths: Option<&RuntimePaths>, message: &str) -> tauri::Result<()> {
    if let Some(paths) = paths {
        append_log(paths, format!("startup error: {message}"));
    } else {
        early_log(format!("startup error before runtime paths were ready: {message}"));
    }

    show_app_window(
        app,
        WebviewUrl::App(Path::new("startup-error.html").into()),
        "HolyFHIR Startup Help",
    )
}

fn main() {
    early_log("HolyFHIR desktop process started");

    tauri::Builder::default()
        .manage(DjangoProcess(Mutex::new(None)))
        .setup(|app| {
            let paths = match runtime_paths(&app.handle()) {
                Ok(paths) => paths,
                Err(error) => {
                    show_startup_error(app, None, &error)?;
                    return Ok(());
                }
            };

            append_log(
                &paths,
                format!(
                    "starting HolyFHIR desktop; app data directory: {:?}",
                    paths.app_data_dir
                ),
            );

            if !is_django_running() {
                if let Err(error) = bootstrap_django(&paths) {
                    show_startup_error(app, Some(&paths), &error)?;
                    return Ok(());
                }

                let child = match start_django(&paths) {
                    Ok(child) => child,
                    Err(error) => {
                        show_startup_error(app, Some(&paths), &error)?;
                        return Ok(());
                    }
                };

                app.state::<DjangoProcess>()
                    .0
                    .lock()
                    .expect("failed to lock Django process state")
                    .replace(child);

                if let Err(error) = wait_for_django() {
                    show_startup_error(app, Some(&paths), &error)?;
                    return Ok(());
                }
            }

            show_app_window(
                app,
                WebviewUrl::External(format!("http://{HOST}:{PORT}/").parse().unwrap()),
                "HolyFHIR Personal EMR",
            )?;

            Ok(())
        })
        .on_window_event(|window, event| {
            if matches!(event, tauri::WindowEvent::CloseRequested { .. }) {
                if let Some(child) = window
                    .state::<DjangoProcess>()
                    .0
                    .lock()
                    .expect("failed to lock Django process state")
                    .as_mut()
                {
                    let _ = child.kill();
                }
            }
        })
        .run(tauri::generate_context!())
        .expect("error while running HolyFHIR desktop app");
}
