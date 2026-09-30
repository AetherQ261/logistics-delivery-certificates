import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.certificate_service import generate_certificate, sample_request


if __name__ == "__main__":
    result = generate_certificate(sample_request())
    print(json.dumps(result, indent=2))
