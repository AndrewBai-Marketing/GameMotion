import SwiftUI
import WebKit

struct ContentView: View {
    @EnvironmentObject var backend: BackendManager

    var body: some View {
        ZStack {
            if backend.isReady {
                GameWebView()
                    .transition(.opacity)
            } else {
                LoadingView()
            }
        }
        .frame(minWidth: 1100, minHeight: 750)
        .animation(.easeInOut(duration: 0.3), value: backend.isReady)
    }
}

// MARK: - Loading screen shown while the Python backend starts up

struct LoadingView: View {
    var body: some View {
        VStack(spacing: 20) {
            Image(systemName: "figure.walk")
                .font(.system(size: 56))
                .foregroundColor(.accentColor)
            ProgressView()
                .scaleEffect(1.3)
            Text("Starting GameMotion…")
                .font(.title3)
                .foregroundColor(.secondary)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Color(NSColor.windowBackgroundColor))
    }
}

// MARK: - WKWebView wrapper

struct GameWebView: NSViewRepresentable {
    private let appURL = URL(string: "http://127.0.0.1:8000/")!

    func makeNSView(context: Context) -> WKWebView {
        let config = WKWebViewConfiguration()
        // Allow the frontend JS to open external links
        let webView = WKWebView(frame: .zero, configuration: config)
        webView.allowsMagnification = false
        webView.navigationDelegate = context.coordinator
        webView.load(URLRequest(url: appURL))
        return webView
    }

    func updateNSView(_ nsView: WKWebView, context: Context) {}

    func makeCoordinator() -> Coordinator { Coordinator(appURL: appURL) }

    class Coordinator: NSObject, WKNavigationDelegate {
        let appURL: URL
        init(appURL: URL) { self.appURL = appURL }

        // If the load fails (backend not quite ready), retry after 1s
        func webView(_ webView: WKWebView, didFailProvisionalNavigation _: WKNavigation!, withError error: Error) {
            print("[WebView] Load failed (\(error.localizedDescription)) — retrying in 1s")
            DispatchQueue.main.asyncAfter(deadline: .now() + 1) {
                webView.load(URLRequest(url: self.appURL))
            }
        }

        // Open external links in the default browser instead of inside the app
        func webView(_ webView: WKWebView, decidePolicyFor action: WKNavigationAction,
                     decisionHandler: @escaping (WKNavigationActionPolicy) -> Void) {
            if action.navigationType == .linkActivated,
               let url = action.request.url,
               url.host != "127.0.0.1" {
                NSWorkspace.shared.open(url)
                decisionHandler(.cancel)
            } else {
                decisionHandler(.allow)
            }
        }
    }
}
