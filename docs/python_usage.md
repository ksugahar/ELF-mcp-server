# Using Product ELF/MAGIC from Python

`elf_mcp_server` provides a high-level Python client (`ElfClient`, `ElfRunResult`, `doctor`) on top of the isolated `ctypes` bridge (`product_runner.py`) so you can drive a user-local ELF600 / MAGIC / ELFIN installation directly from Python scripts.

> **Note:** `elf_mcp_server` does not bundle product DLLs or licenses. You must have a licensed ELF600/MAGIC/ELFIN installation on your machine and point `ELF_PRODUCT_HOME` (or `ELF600_HOME` / `ELF_HOME`) to the directory containing `bin/`.

## 1. Check your environment (`doctor`)

```python
from elf_mcp_server import doctor

report = doctor()
print("OK:", report["ok"])
print("Python bits:", report["python_bits"])
if not report["ok"]:
    for issue in report["issues"]:
        print("Issue:", issue)
```

If `ELF_PRODUCT_HOME` is not set in your environment, you can pass it explicitly:

```python
report = doctor("<path-to-product-installation>")
```

## 2. Run an existing `.mai` / `.meg` case

Use `confirm_product_execution=True` to explicitly authorize local solver execution.

```python
from elf_mcp_server import ElfClient

client = ElfClient(solver="MAGIC", timeout_s=300)
res = client.run_case(work_dir="cases/c_magnet", case_name="c_magnet", confirm_product_execution=True)

if res.ok:
    print(f"Finished in {res.elapsed_s:.2f}s, outputs: {res.outputs}")
    flx_text = res.read_output(".flx")
    rows = res.parse_numeric_table(".flx")
else:
    print("Run failed:", res.error)
```

## 3. Generate `.mai` from Python and run (`run_mai`)

```python
from elf_mcp_server import ElfClient

mai_text = """\
USE  MAGIC  3.50
PRE
  FILE  MESH  demo01.meg
END
SOL  FIXA
END
"""

client = ElfClient(solver="MAGIC")
res = client.run_mai(
    mai_text=mai_text,
    work_dir="runs/demo01",
    case_name="demo01",
    meg_path="assets/model.meg",
    confirm_product_execution=True,
)
print("ok:", res.ok, "outputs:", res.outputs)
```

## 4. Parametric sweep (`sweep`)

```python
from elf_mcp_server import ElfClient

template_mai = """\
USE  MAGIC  3.50
PRE
  FILE  MESH  {case_name}.meg
  CURR  1  {current}
END
SOL  FIXA
END
"""

client = ElfClient(solver="MAGIC")
results = client.sweep(
    template_mai=template_mai,
    params_list=[
        {"current": 100.0},
        {"current": 200.0},
        {"current": 300.0},
    ],
    base_dir="runs/current_sweep",
    meg_path="assets/model.meg",
    confirm_product_execution=True,
)

for item in results:
    res = item["result"]
    print(item["case_name"], item["params"], "ok=", res.ok, "rows=", len(res.parse_numeric_table(".flx")))
```

Both `run_mai` and `sweep` write the .mai and copy a supplied .meg even when confirmation is false. Only solver execution requires confirmation.

The sweep provides `{case_name}` from `case_prefix`. Omit `case_name` from each parameter mapping. Use doubled braces
(`{{` and `}}`) for literal braces in the template.

## Troubleshooting

- **64-bit Python required**: Product DLLs (`magh1600.dll`, `elfh1300.dll`) require 64-bit Python.
- **`ELF product home not found`**: Set `ELF_PRODUCT_HOME` to the folder containing `bin/` or pass `product_home=...` to `ElfClient(...)` / `doctor(...)`.
- **Timeout**: Increase `timeout_s` in `ElfClient(..., timeout_s=1800)` or `run_case(..., timeout_s=1800)`.
