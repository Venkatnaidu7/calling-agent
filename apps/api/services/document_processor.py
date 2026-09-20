class DocumentProcessor:
    async def extract_text(self, content: str | bytes, source_type: str) -> str:
        if source_type == "text":
            return content if isinstance(content, str) else content.decode("utf-8")
        elif source_type == "pdf":
            return self._extract_pdf(content)
        elif source_type == "docx":
            return self._extract_docx(content)
        elif source_type == "url":
            return await self._fetch_url(content)
        elif source_type == "csv":
            return self._extract_csv(content)
        raise ValueError(f"Unsupported source type: {source_type}")

    def _extract_pdf(self, content: bytes) -> str:
        from pypdf import PdfReader
        import io

        reader = PdfReader(io.BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)

    def _extract_docx(self, content: bytes) -> str:
        from docx import Document
        import io

        doc = Document(io.BytesIO(content))
        return "\n".join(para.text for para in doc.paragraphs)

    async def _fetch_url(self, url: str) -> str:
        import httpx
        from bs4 import BeautifulSoup
        import socket
        import ipaddress
        from urllib.parse import urlparse, urljoin

        def _resolve_and_validate(hostname: str) -> str:
            try:
                addr_info = socket.getaddrinfo(hostname, None, socket.AF_INET)
                safe_ip = None
                for entry in addr_info:
                    raw_ip = entry[4][0]
                    ip = ipaddress.ip_address(raw_ip)
                    if (
                        ip.is_private
                        or ip.is_loopback
                        or ip.is_link_local
                        or ip.is_multicast
                        or ip.is_reserved
                    ):
                        raise ValueError(
                            f"Access to internal network addresses is prohibited: {raw_ip}"
                        )
                    safe_ip = raw_ip
                if not safe_ip:
                    raise ValueError(f"No IPv4 address found for {hostname}")
                return safe_ip
            except socket.gaierror as err:
                raise ValueError(f"Could not resolve hostname: {hostname}") from err

        current_url = url
        max_redirects = 3
        response = None

        # verify=False is needed because we connect directly to the IP address, causing hostname mismatch
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            for _ in range(max_redirects + 1):
                parsed = urlparse(current_url)
                if parsed.scheme not in ("http", "https"):
                    raise ValueError(
                        f"Unsupported URL scheme: {parsed.scheme}. Only http and https are allowed."
                    )
                if not parsed.hostname:
                    raise ValueError("Invalid URL hostname")

                safe_ip = _resolve_and_validate(parsed.hostname)
                
                port = parsed.port or (443 if parsed.scheme == "https" else 80)
                safe_url = f"{parsed.scheme}://{safe_ip}:{port}{parsed.path or '/'}"
                if parsed.query:
                    safe_url += f"?{parsed.query}"

                headers = {"Host": parsed.hostname}
                response = await client.get(safe_url, headers=headers, follow_redirects=False)
                
                if response.is_redirect:
                    redirect_location = response.headers.get("Location")
                    if not redirect_location:
                        break
                    current_url = urljoin(current_url, redirect_location)
                else:
                    response.raise_for_status()
                    break
            else:
                raise ValueError("Too many redirects")

        soup = BeautifulSoup(response.text, "lxml")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        return soup.get_text(separator="\n", strip=True)

    def _extract_csv(self, content: str | bytes) -> str:
        import csv
        import io

        if isinstance(content, bytes):
            content = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(content))
        rows = []
        for row in reader:
            rows.append(", ".join(f"{k}: {v}" for k, v in row.items()))
        return "\n".join(rows)
