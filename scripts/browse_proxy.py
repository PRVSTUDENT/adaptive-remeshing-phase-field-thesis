import http.server
import socketserver
import urllib.request
import urllib.parse

PORT = 18080

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        
        target_url = query.get('url', [None])[0]
        if not target_url and self.path != "/":
            if self.path.startswith("/http"):
                target_url = self.path[1:]
        
        if not target_url:
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            html = """
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="utf-8">
                <title>Antigravity Web Search</title>
                <style>
                    body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 25px; background: #1e1e1e; color: #e0e0e0; }
                    .search-box { display: flex; gap: 10px; max-width: 700px; margin: 20px 0; }
                    input[type="text"] { flex: 1; padding: 12px 16px; font-size: 16px; border-radius: 6px; border: 1px solid #444; background: #2d2d2d; color: #fff; }
                    button { padding: 12px 24px; font-size: 16px; border-radius: 6px; border: none; background: #007acc; color: #fff; cursor: pointer; font-weight: 600; }
                    button:hover { background: #0062a3; }
                    iframe { width: 100%; height: 78vh; border: 1px solid #333; border-radius: 8px; background: #fff; margin-top: 15px; }
                    .preset { margin-right: 15px; color: #4daafc; text-decoration: none; font-size: 14px; }
                </style>
            </head>
            <body>
                <h2>Antigravity In-IDE Web Search</h2>
                <div>
                    <a class="preset" href="javascript:void(0)" onclick="setSearch('https://html.duckduckgo.com/html')">DuckDuckGo</a>
                    <a class="preset" href="javascript:void(0)" onclick="setSearch('https://devdocs.io')">DevDocs</a>
                    <a class="preset" href="javascript:void(0)" onclick="setSearch('https://en.wikipedia.org')">Wikipedia</a>
                </div>
                <div class="search-box">
                    <input type="text" id="target" placeholder="Enter search term or URL..." value="https://html.duckduckgo.com/html">
                    <button onclick="loadPage()">Go</button>
                </div>
                <iframe id="viewer" src="/proxy?url=https://html.duckduckgo.com/html"></iframe>

                <script>
                    function setSearch(u) {
                        document.getElementById('target').value = u;
                        loadPage();
                    }
                    function loadPage() {
                        var u = document.getElementById('target').value;
                        if (!u.startsWith('http')) u = 'https://html.duckduckgo.com/html?q=' + encodeURIComponent(u);
                        document.getElementById('viewer').src = '/proxy?url=' + encodeURIComponent(u);
                    }
                </script>
            </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return

        try:
            req = urllib.request.Request(
                target_url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                content_type = resp.headers.get('Content-Type', 'text/html')
                body = resp.read()
                
                if 'text/html' in content_type:
                    try:
                        html_str = body.decode('utf-8', errors='ignore')
                        # Inject <base href="..."> so relative CSS/JS/images load directly
                        base_tag = f'<base href="{target_url}">'
                        if '<head>' in html_str:
                            html_str = html_str.replace('<head>', f'<head>{base_tag}', 1)
                        elif '<HEAD>' in html_str:
                            html_str = html_str.replace('<HEAD>', f'<HEAD>{base_tag}', 1)
                        else:
                            html_str = base_tag + html_str

                        # Rewrite absolute links so clicking them routes through proxy
                        import re
                        def replacer(match):
                            prefix, quote, url = match.group(1), match.group(2), match.group(3)
                            if url.startswith('http://') or url.startswith('https://'):
                                return f'{prefix}{quote}/proxy?url={urllib.parse.quote(url)}{quote}'
                            return match.group(0)
                        html_str = re.sub(r'(href\s*=\s*)(["\'])(http[s]?://[^"\']+)(["\'])', replacer, html_str)
                        body = html_str.encode('utf-8')
                    except Exception:
                        pass

                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h3>Error loading page: {e}</h3>".encode('utf-8'))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        target_url = query.get('url', [None])[0]
        if not target_url:
            target_url = "https://html.duckduckgo.com/html/"

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length) if content_length > 0 else b''

        try:
            req = urllib.request.Request(
                target_url,
                data=post_data,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', 'Content-Type': self.headers.get('Content-Type', 'application/x-www-form-urlencoded')}
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                content_type = resp.headers.get('Content-Type', 'text/html')
                body = resp.read()

                if 'text/html' in content_type:
                    try:
                        html_str = body.decode('utf-8', errors='ignore')
                        base_tag = f'<base href="{target_url}">'
                        if '<head>' in html_str:
                            html_str = html_str.replace('<head>', f'<head>{base_tag}', 1)
                        elif '<HEAD>' in html_str:
                            html_str = html_str.replace('<HEAD>', f'<HEAD>{base_tag}', 1)
                        else:
                            html_str = base_tag + html_str

                        import re
                        def replacer(match):
                            prefix, quote, url = match.group(1), match.group(2), match.group(3)
                            if url.startswith('http://') or url.startswith('https://'):
                                return f'{prefix}{quote}/proxy?url={urllib.parse.quote(url)}{quote}'
                            return match.group(0)
                        html_str = re.sub(r'(href\s*=\s*)(["\'])(http[s]?://[^"\']+)(["\'])', replacer, html_str)
                        body = html_str.encode('utf-8')
                    except Exception:
                        pass

                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.end_headers()
                self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(f"<h3>Error loading page: {e}</h3>".encode('utf-8'))

if __name__ == '__main__':
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(('127.0.0.1', PORT), ProxyHandler) as httpd:
        print(f"Serving local web search proxy at http://localhost:{PORT}")
        httpd.serve_forever()
