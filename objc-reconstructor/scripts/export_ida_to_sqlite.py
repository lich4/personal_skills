import argparse
import json
import os
import sqlite3
import traceback
import sys

idadir = None
for i, arg in enumerate(sys.argv):
    if arg == "--idadir" and i + 1 < len(sys.argv):
        idadir = sys.argv[i+1]
        break

if idadir:
    os.environ["IDADIR"] = idadir
elif "IDADIR" not in os.environ:
    print("Error: Please provide IDA path via --idadir <path> or set IDADIR environment variable.")
    sys.exit(1)

import idapro 
import idaapi
import idautils
import idc

all_exports = list()

def get_name(ea):
    flag = idc.GN_LONG # 其他选项会替换'+', 导致objc识别错误
    return idc.get_name(ea, flag) or ""

def get_valid_type_name(t):
    if not t:
        return ""
    if t.startswith("_UNKNOWN"):
        return ""
    return t

def get_ea_data_type(ea):
    dtype = get_valid_type_name(idc.get_type(ea))
    if not dtype:
        # get_type比guess_type准确
        dtype = get_valid_type_name(idc.guess_type(ea))
    if not dtype:
        ti = idaapi.tinfo_t()
        if idaapi.get_tinfo(ti, ea):
            dtype = ti.get_nice_type_name()
    if not dtype:
        flag = idc.get_full_flags(ea)
        dtype_int = flag & idc.DT_TYPE
        if dtype_int == idc.FF_BYTE:
            dtype = "char"
        elif dtype_int == idc.FF_WORD:
            dtype = "short"
        elif dtype_int == idc.FF_DWORD:
            dtype = "int32_t"
        elif dtype_int == idc.FF_QWORD:
            dtype = "int64_t"
        elif dtype_int == idc.FF_TBYTE:
            dtype = "tbyte"
        elif dtype_int == idc.FF_STRLIT:
            dtype = "char[]"
        elif dtype_int == idc.FF_STRUCT:
            dtype = "struct"
        elif dtype_int == idc.FF_OWORD:
            dtype = "__int128"
        elif dtype_int == idc.FF_FLOAT:
            dtype = "float"
        elif dtype_int == idc.FF_DOUBLE:
            dtype = "double"
    return dtype

def get_struct_obj_from_ea(ea):
    # 从地址数据解析为结构体对象
    ti = idaapi.tinfo_t()
    if idaapi.get_tinfo(ti, ea):
        t_type, t_fields, _ = ti.serialize()
        r, o = idaapi.unpack_object_from_idb(ti.get_til(), t_type, t_fields, ea, 0)
        if r:
            return vars(o)
    return None

def init_db(cursor):
    cursor.executescript('''
        CREATE TABLE IF NOT EXISTS exports (
            ea INTEGER PRIMARY KEY,
            name TEXT,
            ordinal INTEGER
        );
        CREATE TABLE IF NOT EXISTS imports (
            ea INTEGER PRIMARY KEY,
            name TEXT,
            library TEXT,
            ordinal INTEGER
        );
        CREATE TABLE IF NOT EXISTS symbols (
            ea INTEGER PRIMARY KEY,
            name TEXT,
            type TEXT,
            dtype TEXT,
            dsize INTEGER,
            xrefs TEXT
        );
        CREATE TABLE IF NOT EXISTS functions (
            ea INTEGER PRIMARY KEY,
            end_ea INTEGER,
            name TEXT,
            proto TEXT,
            xrefs TEXT
        );
        CREATE TABLE IF NOT EXISTS strings (
            ea INTEGER PRIMARY KEY,
            len INTEGER,
            str TEXT
        );
        CREATE TABLE IF NOT EXISTS segments (
            start_ea INTEGER PRIMARY KEY,
            end_ea INTEGER,
            name TEXT,
            class TEXT,
            perm INTEGER,
            bit INTEGER
        );
        CREATE TABLE IF NOT EXISTS types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            size INTEGER,
            type TEXT,
            proto TEXT
        );
        CREATE TABLE IF NOT EXISTS asm_codes (
            ea INTEGER PRIMARY KEY,
            code TEXT
        );
        CREATE TABLE IF NOT EXISTS pseudo_codes (
            ea INTEGER PRIMARY KEY,
            code TEXT
        );
        CREATE TABLE IF NOT EXISTS data_items (
            ea INTEGER PRIMARY KEY,
            size INTEGER,
            type TEXT,
            raw BLOB
        );
    ''')

all_exports.append("exports")
def export_exports(cursor):
    print("Exporting exports...")
    for i, ordinal, ea, name in idautils.Entries():
        cursor.execute('INSERT OR REPLACE INTO exports (ea, name, ordinal) VALUES (?, ?, ?)', 
            (ea, name, ordinal))

all_exports.append("imports")
def export_imports(cursor):
    print("Exporting imports...")
    qty = idaapi.get_import_module_qty()
    for i in range(qty):
        library = idaapi.get_import_module_name(i) or "<unnamed>"
        def imp_cb(ea, name, ordinal):
            cursor.execute('INSERT OR REPLACE INTO imports (ea, name, library, ordinal) VALUES (?, ?, ?, ?)', 
                (ea, name, library, ordinal))
            return True
        idaapi.enum_import_names(i, imp_cb)

all_exports.append("symbols")
def export_symbols(cursor):
    print("Exporting symbols...")
    for sym_ea, sym_name in idautils.Names():
        flag = idc.get_full_flags(sym_ea)
        type_int = flag & idc.MS_CLS
        dsize = 0
        dtype = ""
        if type_int == idc.FF_CODE:
            type_str = "CODE"
        elif type_int == idc.FF_DATA:
            type_str = "DATA"
            dsize = idc.get_item_size(sym_ea)
            dtype = get_ea_data_type(sym_ea)
        else:
            type_str = "UNKNOWN" # unknown class/size/type
        xrefs = list()
        for xref in idautils.XrefsFrom(sym_ea, idaapi.XREF_NOFLOW):
            if not idaapi.is_mapped(xref.to):
                continue
            xrefs.append({"ea": xref.to, "name": get_name(xref.to)})
        xrefs_raw = json.dumps(xrefs)
        cursor.execute('INSERT OR REPLACE INTO symbols (ea, name, type, dtype, dsize, xrefs) VALUES (?, ?, ?, ?, ?, ?)', 
            (sym_ea, sym_name, type_str, dtype, dsize, xrefs_raw))

all_exports.append("functions")
def export_functions(cursor):
    print("Exporting functions...")
    for func_ea in idautils.Functions():
        func = idaapi.get_func(func_ea)
        name = get_name(func_ea) # 为保持一致性不用func.name
        proto = func.get_prototype().dstr() if func.get_prototype() else ""
        end_ea = func.end_ea
        xrefs = list()
        for ea in idautils.Heads(func_ea, end_ea):
            for xref in idautils.XrefsFrom(ea, idaapi.XREF_NOFLOW):
                if not idaapi.is_mapped(xref.to):
                    continue
                xrefs.append({"ea": xref.to, "name": get_name(xref.to)})
        xrefs_raw = json.dumps(xrefs)
        cursor.execute('INSERT OR REPLACE INTO functions (ea, end_ea, name, proto, xrefs) VALUES (?, ?, ?, ?, ?)', 
            (func_ea, end_ea, name, proto, xrefs_raw))

all_exports.append("strings")
def export_strings(cursor):
    print("Exporting strings...")
    for s in idautils.Strings():
        cursor.execute('INSERT OR REPLACE INTO strings (ea, len, str) VALUES (?, ?, ?)', 
            (s.ea, s.length, str(s)))

all_exports.append("segments")
def export_segments(cursor):
    print("Exporting segments...")
    for n in range(idaapi.get_segm_qty()):
        seg = idaapi.getnseg(n)
        name = idaapi.get_segm_name(seg)
        sclass = idaapi.get_segm_class(seg) or ""
        cursor.execute('INSERT OR REPLACE INTO segments (start_ea, end_ea, name, class, perm, bit) VALUES (?, ?, ?, ?, ?, ?)', 
            (seg.start_ea, seg.end_ea, name, sclass, seg.perm, seg.bitness))

all_exports.append("types")
def export_types(cursor):
    print("Exporting types...")
    til = idaapi.get_idati()
    qty = idaapi.get_ordinal_limit(til)
    for i in range(1, qty):
        ti = til.get_numbered_type(i)
        name = ti.get_nice_type_name()
        if not name:
            continue
        size = ti.get_size()
        size = 0 if size == idaapi.BADSIZE else size
        type_int = ti.get_realtype()
        type_str = "UNKNOWN"
        base_type = type_int & idaapi.TYPE_BASE_MASK
        if base_type == idaapi.BT_UNK:
            type_str = "UNKNOWN"
        elif base_type == idaapi.BT_VOID:
            type_str = "VOID"
        elif base_type == idaapi.BT_INT8:
            type_str = "INT8"
        elif base_type == idaapi.BT_INT16:
            type_str = "INT16"
        elif base_type == idaapi.BT_INT32:
            type_str = "INT32"
        elif base_type == idaapi.BT_INT64:
            type_str = "INT64"
        elif base_type == idaapi.BT_INT128:
            type_str = "INT128"
        elif base_type == idaapi.BT_INT:
            type_str = "INT"
        elif base_type == idaapi.BT_BOOL:
            type_str = "BOOL"
        elif base_type == idaapi.BT_FLOAT:
            type_str = "FLOAT"
        elif base_type == idaapi.BT_PTR:
            type_str = "PTR"
        elif base_type == idaapi.BT_ARRAY:
            type_str = "ARRAY"
        elif base_type == idaapi.BT_FUNC:
            type_str = "FUNC"
        elif base_type == idaapi.BT_COMPLEX:
            type_flags = type_int & idaapi.TYPE_FLAGS_MASK
            if type_flags == idaapi.BTMT_STRUCT:
                type_str = "STRUCT"
            elif type_flags == idaapi.BTMT_UNION:
                type_str = "UNION"
            elif type_flags == idaapi.BTMT_ENUM:
                type_str = "ENUM"
            elif type_flags == idaapi.BTMT_TYPEDEF:
                type_str = "TYPEDEF"
        elif base_type == idaapi.BT_BITFIELD:
            type_str = "BITFIELD"
        flags = idaapi.PRTYPE_MULTI | idaapi.PRTYPE_TYPE | idaapi.PRTYPE_OFFSETS | idaapi.PRTYPE_DEF
        proto = ti._print(ti.get_nice_type_name(), flags, 2)
        cursor.execute('INSERT INTO types (name, size, type, proto) VALUES (?, ?, ?, ?)', 
            (name, size, type_str, proto))

all_exports.append("asm_codes")
def export_asm_codes(cursor, config):
    print("Exporting asm_codes...")
    # todo: 
    # 1. 需要config限制, 否则数目过多
    # 2. 增量更新
    for func_ea in idautils.Functions():
        lines = list()
        for chunk_start, chunk_end in idautils.Chunks(func_ea):
            for ea in idautils.Heads(chunk_start, chunk_end):
                asm = idc.generate_disasm_line(ea, 0)
                if asm:
                    lines.append(f"{ea:08x}  {asm}")
        code = "\n".join(lines)
        cursor.execute('INSERT OR REPLACE INTO asm_codes (ea, code) VALUES (?, ?)', (func_ea, code))

all_exports.append("pseudo_codes")
def export_pseudo_codes(cursor, config):
    print("Exporting pseudo_codes...")
    # todo: 
    # 1. 需要config限制, 否则数目过多
    # 2. 增量更新
    if not idaapi.init_hexrays_plugin():
        print("Error: no hexray")
        return
    for func_ea in idautils.Functions():
        try:
            cfunc = idaapi.decompile(func_ea)
            code = str(cfunc)
        except Exception as e:
            print(f"Error: Decompile failed: {e}")
            code = "/* DECOMPILATION FAILED */"
        cursor.execute('INSERT OR REPLACE INTO pseudo_codes (ea, code) VALUES (?, ?)', (func_ea, code))

all_exports.append("data_items")
def export_data_items(cursor):
    print("Exporting data_items...")
    for seg_ea in idautils.Segments():
        seg_end = idc.get_segm_end(seg_ea)
        for ea in idautils.Heads(seg_ea, seg_end):
            flags = idaapi.get_flags(ea)
            if not idaapi.is_data(flags):
                continue
            size = idaapi.get_item_size(ea)
            type_str = get_ea_data_type(ea)
            raw_bytes = idaapi.get_bytes(ea, size)
            cursor.execute('INSERT OR REPLACE INTO data_items (ea, size, type, raw) VALUES (?, ?, ?, ?)',
                (ea, size, type_str, raw_bytes))


def main():
    parser = argparse.ArgumentParser(description="Export idapro analysis data to sqlite")
    parser.add_argument("-i", "--input", required=True, help="Specify input binary path (MachO/ELF/PE)")
    parser.add_argument("-o", "--output", required=True, help="Specify output sqlite database path")
    parser.add_argument("-e", "--export", default="all", help="Specify data types to dump, comma-separated, e.g., 'functions,strings', default: all")
    config = parser.parse_args()
    if config.export == "all":
        to_export = list(all_exports)
    elif config.export == "base":
        to_export = [i for i in all_exports if i not in ["asm_codes", "pseudo_codes"]]
    else:
        to_export = config.export.split(',')
    bin_path = config.input
    db_path = config.output
    if not os.path.exists(bin_path):
        print(f"Error: Input file not found {bin_path}")
        exit(-1)
    print(f"Opening idapro database for {bin_path}")
    r = idapro.open_database(bin_path, True) 
    if r != 0: 
        print(f"Error: Opening idapro database failed") 
        exit(0)
    print(f"Open idapro database success!")
    conn = None
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        init_db(cursor)
        if "exports" in to_export:
            export_exports(cursor)
        if "imports" in to_export:
            export_imports(cursor)
        if "symbols" in to_export:
            export_symbols(cursor)
        if "functions" in to_export:
            export_functions(cursor)
        if "strings" in to_export:
            export_strings(cursor)
        if "segments" in to_export:
            export_segments(cursor)
        if "types" in to_export:
            export_types(cursor)
        if "data_items" in to_export:
            export_data_items(cursor)
        if "asm_codes" in to_export:
            export_asm_codes(cursor, config)
        if "pseudo_codes" in to_export:
            export_pseudo_codes(cursor, config)
        conn.commit()
        print("Export done!")
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()
    if conn is not None:
        conn.close()
    idapro.close_database()

if __name__ == '__main__':
    main()

