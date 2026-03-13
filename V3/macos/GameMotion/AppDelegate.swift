import AppKit
import ApplicationServices

class AppDelegate: NSObject, NSApplicationDelegate {
    let backendManager = BackendManager()

    func applicationDidFinishLaunching(_ notification: Notification) {
        backendManager.start()
        checkAccessibilityPermission()
    }

    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        return true
    }

    func applicationWillTerminate(_ notification: Notification) {
        backendManager.stop()
    }

    private func checkAccessibilityPermission() {
        guard !AXIsProcessTrusted() else { return }

        DispatchQueue.main.asyncAfter(deadline: .now() + 2.0) {
            let alert = NSAlert()
            alert.messageText = "Enable Accessibility Access"
            alert.informativeText = """
                GameMotion needs Accessibility access to send keystrokes to your games.

                Please go to System Settings → Privacy & Security → Accessibility \
                and enable GameMotion, then restart the app.
                """
            alert.alertStyle = .informational
            alert.addButton(withTitle: "Open System Settings")
            alert.addButton(withTitle: "Later")

            if alert.runModal() == .alertFirstButtonReturn {
                let url = URL(string: "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility")!
                NSWorkspace.shared.open(url)
            }
        }
    }
}
