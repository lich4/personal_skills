## Tables

### exports

Stores the functions and variables that this binary exports for use by other modules. Relates to `ida_entry.py`. Important for understanding the API surface of a library being reversed.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `ea` | INTEGER PRIMARY KEY | The linear address of the exported symbol. |
| `name` | TEXT | The exported name. |
| `ordinal` | INTEGER | The export ordinal number. |

### imports

Stores the functions and variables imported from external libraries (e.g., DLLs, shared objects). Relates to `ida_nalt.py` and `ida_loader.py`. Knowing external dependencies is critical for reconstructing full projects.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `ea` | INTEGER PRIMARY KEY | The linear address of the import table entry (e.g., IAT address in PE or GOT address in ELF). |
| `name` | TEXT | The name of the imported function or variable. |
| `library` | TEXT | The name of the module/library it is imported from (e.g., `kernel32.dll`, `libc.so.6`). |
| `ordinal` | INTEGER | The import ordinal number, if imported by ordinal instead of name. NULL if imported by name. |

### symbols

Stores named locations (symbols) in the binary, mapping human-readable names to virtual addresses. Relates to `ida_name.py` and `ida_entry.py`.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `ea` | INTEGER PRIMARY KEY | The linear address of the symbol. |
| `name` | TEXT | The name of the symbol. |
| `type` | TEXT | The type of the symbol. (e.g., `CODE`, `DATA`, `UNKNOWN`) |
| `dtype` | TEXT | The type of the data inferred by IDAPro. |
| `dsize` | TEXT | The size of the data inferred by IDAPro. |
| `xrefs` | TEXT | A JSON list of outgoing cross-references (xrefs from the symbol). Format: `[{"ea": target_ea, "name": target_name}]`. |

### functions

Stores information about all functions defined in the binary. This corresponds to the concepts in `ida_funcs.py`. It is crucial for understanding the high-level boundaries of executable code.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `ea` | INTEGER PRIMARY KEY | The entry address (linear address) of the function. |
| `end_ea` | INTEGER | The end address of the function. |
| `name` | TEXT | The name of the function. |
| `proto` | TEXT | C-style declaration (prototype) of the function. |
| `xrefs` | TEXT | A JSON list of outgoing cross-references (xrefs from the symbol). Format: `[{"ea": target_ea, "name": target_name}]`. |

### strings

Stores the extracted string literals from the binary data. Relates to `ida_strlist.py`. Strings are highly informative for an LLM inferring functionality.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `ea` | INTEGER PRIMARY KEY | The linear address where the string is located. |
| `len` | INTEGER | The length of the string in characters (or bytes). |
| `str` | TEXT | The actual string content, properly escaped. |

### segments

Stores information about the memory segments in the disassembled program, derived from `ida_segment.py`. This defines the memory layout of the binary.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `start_ea` | INTEGER PRIMARY KEY | The start address of the segment. |
| `end_ea` | INTEGER | The end address of the segment (exclusive). |
| `name` | TEXT | The name of the segment (e.g., `.text`, `.data`, `.bss`). |
| `class` | TEXT | The segment class (e.g., `CODE`, `DATA`, `BSS`, `CONST`). |
| `perm` | INTEGER | The memory permissions of the segment (Read=4, Write=2, Execute=1). |
| `bit` | INTEGER | The addressing bitness of the segment (e.g., 16, 32, 64). |

### types

Stores user-defined types (UDTs), including structures, unions, typedefs, and enums, based on `ida_typeinf.py` concepts (`tinfo_t`, `til_t`). Essential for recovering complex data structures. Complex types like structs merge their member definitions directly into the `decl` field as commented C-code.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `id` | INTEGER PRIMARY KEY AUTOINCREMENT | Unique internal identifier for the type. |
| `name` | TEXT | The name of the type (e.g., `struct _PEB`). |
| `size` | INTEGER | The total size of the type in bytes. |
| `type` | TEXT | The category of the type (e.g., `BASIC`, `STRUCT`, `UNION`, `ENUM`, `TYPEDEF`). |
| `proto` | TEXT | The C-style declaration string. |

### asm_codes

Stores the complete disassembly code blocks. Rather than storing instruction by instruction, this stores the aggregated assembly text, which is more token-efficient and contextual for LLMs.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `ea` | INTEGER PRIMARY KEY | The entry address of the function or the start address of the code block. |
| `code` | TEXT | The full assembly code for this function/block, formatted as a multi-line string. |

### pseudo_codes

Stores the Hex-Rays decompiler output (ctree C pseudo-code) for functions. Corresponds to `ida_hexrays.py`. This is the most crucial part for an LLM to quickly understand the binary logic without reading assembly.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `ea` | INTEGER PRIMARY KEY | The entry address of the function (Foreign Key to `functions.ea`). |
| `code` | TEXT | Full pseudo code if success, and comment with the error cause if failure. |

### data_items

Tracks globally defined data items in memory, separate from executable code. Relates to `ida_bytes.py` (checking flags for data, words, dwords, arrays, etc.). This helps the LLM distinguish between static configuration/data and executable logic.

| Field Name | SQLite Type | Description |
| :--- | :--- | :--- |
| `ea` | INTEGER PRIMARY KEY | The linear address of the data item. |
| `size` | INTEGER | The total size of the data item in bytes. |
| `type` | TEXT | The C-style declaration string. |
| `raw` | BLOB | The raw bytes of the data. |

