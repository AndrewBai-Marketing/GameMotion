import Foundation
import Combine

class BackendManager: ObservableObject {
    @Published var isReady = false

    private var process: Process?
    private var healthTimer: Timer?

    func start() {
        guard let resourcePath = Bundle.main.resourcePath else {
            print("[BackendManager] Could not resolve resource path")
            return
        }

        // Mirrors the Electron layout:
        //   Resources/backend/GameMotionBackend/GameMotionBackend  (exe)
        //   Resources/frontend/                                     (Next.js static export)
        let backendDir = resourcePath + "/backend/GameMotionBackend"
        let backendExe = backendDir + "/GameMotionBackend"
        let frontendDir = resourcePath + "/frontend"

        guard FileManager.default.fileExists(atPath: backendExe) else {
            print("[BackendManager] Backend binary not found: \(backendExe)")
            return
        }

        let dataDir = applicationSupportDir()

        let proc = Process()
        proc.executableURL = URL(fileURLWithPath: backendExe)
        proc.arguments = ["--static-dir", frontendDir]
        proc.currentDirectoryURL = URL(fileURLWithPath: backendDir)

        var env = ProcessInfo.processInfo.environment
        env["GAMEMOTION_DATA_DIR"] = dataDir
        proc.environment = env

        let stdout = Pipe()
        let stderr = Pipe()
        proc.standardOutput = stdout
        proc.standardError = stderr

        let logURL = URL(fileURLWithPath: "/tmp/gamemotion_backend.log")
        try? "".write(to: logURL, atomically: true, encoding: .utf8)
        let logHandle = try? FileHandle(forWritingTo: logURL)

        stdout.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            if !data.isEmpty {
                logHandle?.write(data)
                if let line = String(data: data, encoding: .utf8) {
                    print("[backend] \(line.trimmingCharacters(in: .whitespacesAndNewlines))")
                }
            }
        }
        stderr.fileHandleForReading.readabilityHandler = { handle in
            let data = handle.availableData
            if !data.isEmpty {
                logHandle?.write(data)
                if let line = String(data: data, encoding: .utf8) {
                    print("[backend] \(line.trimmingCharacters(in: .whitespacesAndNewlines))")
                }
            }
        }
        proc.terminationHandler = { p in
            print("[BackendManager] Backend exited (code \(p.terminationStatus))")
        }

        do {
            try proc.run()
            self.process = proc
            print("[BackendManager] Backend started (pid \(proc.processIdentifier))")
            pollHealth()
        } catch {
            print("[BackendManager] Failed to start backend: \(error)")
        }
    }

    func stop() {
        healthTimer?.invalidate()
        healthTimer = nil
        process?.terminate()
        process = nil
    }

    // Poll /health every 500ms until the backend is up (max 30s).
    private func pollHealth() {
        let url = URL(string: "http://127.0.0.1:8000/health")!
        var attempts = 0

        healthTimer = Timer.scheduledTimer(withTimeInterval: 0.5, repeats: true) { [weak self] timer in
            guard let self else { timer.invalidate(); return }
            attempts += 1

            URLSession.shared.dataTask(with: url) { _, response, _ in
                if let http = response as? HTTPURLResponse, http.statusCode == 200 {
                    timer.invalidate()
                    DispatchQueue.main.async { self.isReady = true }
                    print("[BackendManager] Backend healthy after \(attempts) polls")
                }
            }.resume()

            if attempts > 60 {
                timer.invalidate()
                DispatchQueue.main.async { self.isReady = true }
                print("[BackendManager] Health timeout — loading anyway")
            }
        }
    }

    private func applicationSupportDir() -> String {
        let urls = FileManager.default.urls(for: .applicationSupportDirectory, in: .userDomainMask)
        let dir = urls[0].appendingPathComponent("GameMotion")
        try? FileManager.default.createDirectory(at: dir, withIntermediateDirectories: true)
        return dir.path
    }
}
