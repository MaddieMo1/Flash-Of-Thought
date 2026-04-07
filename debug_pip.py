from pip._vendor.packaging.version import Version

versions = ["3.12.0", "3.12", "3.12.0b3", "3.12.1"]

for v_str in versions:
    try:
        v = Version(v_str)
        print(f"Version('{v_str}') is valid: {v}")
    except Exception as e:
        print(f"Version('{v_str}') is INVALID: {e}")
