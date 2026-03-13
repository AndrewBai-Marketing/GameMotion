import SwiftUI

@main
struct GameMotionApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) var appDelegate

    var body: some Scene {
        WindowGroup("GameMotion") {
            ContentView()
                .environmentObject(appDelegate.backendManager)
        }
        .windowStyle(.titleBar)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}
