package com.insaatai.app;

import android.app.DownloadManager;
import android.content.ActivityNotFoundException;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.Insets;
import android.net.Uri;
import android.net.http.SslError;
import android.os.Build;
import android.os.Bundle;
import android.os.Environment;
import android.print.PrintAttributes;
import android.print.PrintManager;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.webkit.CookieManager;
import android.webkit.URLUtil;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.webkit.SslErrorHandler;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.Toast;

public final class MainActivity extends android.app.Activity {
    private static final int FILE_CHOOSER_REQUEST = 4107;
    private static final String APP_HOST = "insaat-ai.onrender.com";
    private static final int APP_BACKGROUND = Color.rgb(11, 15, 23);

    private WebView webView;
    private ProgressBar progressBar;
    private ValueCallback<Uri[]> pendingFileChooser;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().setStatusBarColor(APP_BACKGROUND);
        getWindow().setNavigationBarColor(APP_BACKGROUND);
        if (Build.VERSION.SDK_INT >= 29) {
            getWindow().setNavigationBarContrastEnforced(false);
            getWindow().setStatusBarContrastEnforced(false);
        }

        LinearLayout root = new LinearLayout(this);
        root.setOrientation(LinearLayout.VERTICAL);
        root.setBackgroundColor(APP_BACKGROUND);
        if (Build.VERSION.SDK_INT >= 35) {
            getWindow().setDecorFitsSystemWindows(false);
            root.setOnApplyWindowInsetsListener((view, insets) -> {
                Insets bars = insets.getInsets(
                    WindowInsets.Type.systemBars() | WindowInsets.Type.displayCutout()
                );
                view.setPadding(bars.left, bars.top, bars.right, bars.bottom);
                return WindowInsets.CONSUMED;
            });
        }

        progressBar = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        progressBar.setMax(100);
        progressBar.setProgress(0);
        progressBar.setProgressTintList(android.content.res.ColorStateList.valueOf(0xFF8B5CF6));
        progressBar.setIndeterminateTintList(android.content.res.ColorStateList.valueOf(0xFF8B5CF6));
        root.addView(progressBar, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, dp(3)
        ));

        webView = new WebView(this);
        webView.setBackgroundColor(APP_BACKGROUND);
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);
        configureWebView();
        root.addView(webView, new LinearLayout.LayoutParams(
            ViewGroup.LayoutParams.MATCH_PARENT, 0, 1f
        ));
        setContentView(root);

        if (savedInstanceState == null) {
            webView.loadUrl(getString(R.string.app_home_url));
        } else {
            webView.restoreState(savedInstanceState);
        }
    }

    private void configureWebView() {
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setLoadWithOverviewMode(true);
        settings.setUseWideViewPort(true);
        settings.setSupportZoom(false);
        settings.setBuiltInZoomControls(false);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);

        CookieManager cookieManager = CookieManager.getInstance();
        cookieManager.setAcceptCookie(true);
        cookieManager.setAcceptThirdPartyCookies(webView, false);

        webView.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri = request.getUrl();
                String scheme = uri.getScheme() == null ? "" : uri.getScheme();
                String host = uri.getHost() == null ? "" : uri.getHost();
                if ("insaat-ai".equalsIgnoreCase(scheme) && "print".equalsIgnoreCase(host)) {
                    printCurrentPage();
                    return true;
                }
                if ("https".equalsIgnoreCase(scheme) && APP_HOST.equalsIgnoreCase(host)) {
                    return false;
                }
                if ("https".equalsIgnoreCase(scheme) || "http".equalsIgnoreCase(scheme)) {
                    openExternal(uri);
                }
                return true;
            }

            @Override
            public void onPageStarted(WebView view, String url, android.graphics.Bitmap favicon) {
                progressBar.setVisibility(View.VISIBLE);
                progressBar.setProgress(8);
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                progressBar.setVisibility(View.GONE);
                CookieManager.getInstance().flush();
                view.evaluateJavascript(
                    "window.print=function(){window.location.href='insaat-ai://print';};",
                    null
                );
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showOfflinePage();
                }
            }

            @Override
            public void onReceivedSslError(WebView view, SslErrorHandler handler, SslError error) {
                handler.cancel();
            }
        });

        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int progress) {
                progressBar.setProgress(progress);
                progressBar.setVisibility(progress >= 100 ? View.GONE : View.VISIBLE);
            }

            @Override
            public boolean onShowFileChooser(
                WebView view,
                ValueCallback<Uri[]> filePathCallback,
                FileChooserParams fileChooserParams
            ) {
                if (pendingFileChooser != null) {
                    pendingFileChooser.onReceiveValue(null);
                }
                pendingFileChooser = filePathCallback;
                try {
                    startActivityForResult(
                        fileChooserParams.createIntent(), FILE_CHOOSER_REQUEST
                    );
                    return true;
                } catch (ActivityNotFoundException exception) {
                    pendingFileChooser = null;
                    filePathCallback.onReceiveValue(null);
                    Toast.makeText(MainActivity.this, "Dosya seçici açılamadı.", Toast.LENGTH_SHORT).show();
                    return false;
                }
            }
        });

        webView.setDownloadListener((url, userAgent, contentDisposition, mimeType, contentLength) -> {
            Uri uri = Uri.parse(url);
            if (!"https".equalsIgnoreCase(uri.getScheme())
                || !APP_HOST.equalsIgnoreCase(uri.getHost())) {
                openExternal(uri);
                return;
            }
            DownloadManager.Request request = new DownloadManager.Request(uri);
            request.setTitle(URLUtil.guessFileName(url, contentDisposition, mimeType));
            request.setDescription("İnşaat AI raporu indiriliyor");
            request.setMimeType(mimeType);
            request.addRequestHeader("User-Agent", userAgent);
            String cookies = CookieManager.getInstance().getCookie(url);
            if (cookies != null) {
                request.addRequestHeader("Cookie", cookies);
            }
            request.setNotificationVisibility(
                DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED
            );
            request.setDestinationInExternalPublicDir(
                Environment.DIRECTORY_DOWNLOADS,
                URLUtil.guessFileName(url, contentDisposition, mimeType)
            );
            DownloadManager manager = (DownloadManager) getSystemService(DOWNLOAD_SERVICE);
            if (manager != null) {
                manager.enqueue(request);
                Toast.makeText(this, "İndirme başlatıldı.", Toast.LENGTH_SHORT).show();
            }
        });
    }

    private void showOfflinePage() {
        progressBar.setVisibility(View.GONE);
        String html = "<!doctype html><html lang='tr'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            + "<meta charset='utf-8'><body style='margin:0;background:#0b0f17;color:#f8fafc;"
            + "font:16px system-ui;min-height:100vh;display:grid;place-items:center;text-align:center'>"
            + "<main style='padding:28px;max-width:420px'><div style='font-size:48px'>📡</div>"
            + "<h1>Bağlantı kurulamadı</h1><p style='color:#aab4c4'>İnternet bağlantını kontrol edip yeniden dene.</p>"
            + "<button onclick=\"location.href='" + getString(R.string.app_home_url) + "'\" "
            + "style='border:0;border-radius:14px;padding:14px 22px;background:#8b5cf6;color:white;font-size:16px'>"
            + "Yeniden dene</button></main></body></html>";
        webView.loadDataWithBaseURL(
            getString(R.string.app_home_url), html, "text/html", "UTF-8", null
        );
    }

    private void openExternal(Uri uri) {
        try {
            startActivity(new Intent(Intent.ACTION_VIEW, uri));
        } catch (ActivityNotFoundException ignored) {
            Toast.makeText(this, "Bu bağlantı açılamadı.", Toast.LENGTH_SHORT).show();
        }
    }

    private void printCurrentPage() {
        PrintManager printManager = (PrintManager) getSystemService(PRINT_SERVICE);
        if (printManager == null || webView == null) {
            Toast.makeText(this, "PDF yazdırma açılamadı.", Toast.LENGTH_SHORT).show();
            return;
        }
        String jobName = "Insaat-AI-Rapor";
        printManager.print(
            jobName,
            webView.createPrintDocumentAdapter(jobName),
            new PrintAttributes.Builder().build()
        );
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode == FILE_CHOOSER_REQUEST && pendingFileChooser != null) {
            Uri[] results = resultCode == RESULT_OK && data != null
                ? WebChromeClient.FileChooserParams.parseResult(resultCode, data)
                : null;
            pendingFileChooser.onReceiveValue(results);
            pendingFileChooser = null;
        }
    }

    @Override
    protected void onSaveInstanceState(Bundle outState) {
        if (webView != null) {
            webView.saveState(outState);
        }
        super.onSaveInstanceState(outState);
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }

    @Override
    protected void onPause() {
        if (webView != null) {
            webView.onPause();
        }
        super.onPause();
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
        }
    }

    @Override
    protected void onDestroy() {
        if (pendingFileChooser != null) {
            pendingFileChooser.onReceiveValue(null);
            pendingFileChooser = null;
        }
        if (webView != null) {
            webView.stopLoading();
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
