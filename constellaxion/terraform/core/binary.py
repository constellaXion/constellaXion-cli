import os
import sys
import platform
import zipfile
import requests
from pathlib import Path
from tqdm import tqdm

from constellaxion.terraform.core.enums import TERRAFORM_VERSION


class TerraformBinary:
    """Manages terraform binary download and caching.
    
    This class handles platform-specific terraform binary management,
    including downloading from HashiCorp releases, caching locally,
    and ensuring the binary is executable.
    
    Attributes:
        version: Terraform version to manage
        _cache_dir: Directory where binaries are cached
        _binary_path: Path to the terraform binary
    """
    
    def __init__(self, version: str = TERRAFORM_VERSION) -> None:
        """Initialize terraform binary manager.
        
        Args:
            version: Terraform version to download and manage.
                Defaults to TERRAFORM_VERSION constant.
        """
        self.version = version
        self._cache_dir = self._get_cache_dir()
        self._binary_path = self._get_binary_path()
    
    def get_path(self) -> Path:
        """Get path to terraform binary, downloading if necessary.
        
        Returns:
            Path to the terraform binary executable.
            
        Raises:
            ConnectionError: If download fails due to network issues.
            ValueError: If downloaded file is invalid.
            NotImplementedError: If platform is not supported.
        """
        if not self._binary_path.exists():
            self._download_binary()
        return self._binary_path
    
    def is_available(self) -> bool:
        """Check if terraform binary is available locally.
        
        Returns:
            True if binary exists and is accessible, False otherwise.
        """
        return self._binary_path.exists()
    
    def get_version(self) -> str:
        """Get the configured terraform version.
        
        Returns:
            The terraform version string.
        """
        return self.version
    
    def _get_binary_path(self) -> Path:
        """Get the expected path to the terraform binary.
        
        Returns:
            Path where the terraform binary should be located.
        """
        binary_name = "terraform.exe" if sys.platform == "win32" else "terraform"
        return self._cache_dir / binary_name
    
    def _download_binary(self) -> None:
        """Download terraform binary for current platform.
        
        Downloads the appropriate terraform binary for the current platform
        and architecture from HashiCorp's official releases.
        
        Raises:
            NotImplementedError: If platform/architecture is not supported.
            ConnectionError: If download fails.
            ValueError: If downloaded file is not a valid zip.
        """
        print(f"Downloading Terraform v{self.version}...")
        
        # Determine platform and architecture
        os_name_map = {
            'darwin': 'darwin',
            'linux': 'linux', 
            'win32': 'windows'
        }
        arch_map = {
            'x86_64': 'amd64',
            'AMD64': 'amd64',
            'aarch64': 'arm64',
            'arm64': 'arm64'
        }
        
        os_name = os_name_map.get(sys.platform)
        arch = arch_map.get(platform.machine())
        
        if not os_name or not arch:
            raise NotImplementedError(
                f"Unsupported platform: {sys.platform} {platform.machine()}. "
                f"Supported platforms: {list(os_name_map.keys())}. "
                f"Supported architectures: {list(arch_map.keys())}"
            )
        
        # Download and extract
        zip_name = f"terraform_{self.version}_{os_name}_{arch}.zip"
        url = f"https://releases.hashicorp.com/terraform/{self.version}/{zip_name}"
        
        self._download_and_extract(url, zip_name)
        
        # Make executable on Unix systems
        if sys.platform != "win32":
            os.chmod(self._binary_path, 0o755)
        
        print("Terraform download complete.")
    
    def _download_and_extract(self, url: str, zip_name: str) -> None:
        """Download zip file and extract terraform binary.
        
        Args:
            url: URL to download the terraform zip file from.
            zip_name: Name of the zip file for display purposes.
            
        Raises:
            ConnectionError: If download fails due to network issues.
            ValueError: If downloaded file is not a valid zip.
        """
        zip_path = self._cache_dir / zip_name
        
        try:
            # Download with progress bar
            response = requests.get(url, stream=True, timeout=300)
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            
            with open(zip_path, 'wb') as f, tqdm(
                desc=zip_name,
                total=total_size,
                unit='iB',
                unit_scale=True,
                unit_divisor=1024,
            ) as bar:
                for chunk in response.iter_content(chunk_size=1024):
                    if chunk:  # Filter out keep-alive chunks
                        f.write(chunk)
                        bar.update(len(chunk))
            
            # Extract binary
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self._cache_dir)
            
            # Clean up zip file
            zip_path.unlink()
            
        except requests.exceptions.RequestException as e:
            if zip_path.exists():
                zip_path.unlink()  # Clean up partial download
            raise ConnectionError(f"Failed to download Terraform: {e}")
        except zipfile.BadZipFile as e:
            if zip_path.exists():
                zip_path.unlink()  # Clean up invalid file
            raise ValueError(f"Downloaded file is not a valid zip: {e}")
    
    def _get_cache_dir(self) -> Path:
        """Get platform-appropriate cache directory.
        
        Returns:
            Path to the cache directory, creating it if necessary.
        """
        if sys.platform == "win32":
            cache_path = Path(os.environ["LOCALAPPDATA"]) / "Constellaxion" / "Cache"
        elif sys.platform == "darwin":
            cache_path = Path.home() / "Library" / "Caches" / "Constellaxion"
        else:
            cache_path = Path.home() / ".cache" / "constellaxion"
        
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path