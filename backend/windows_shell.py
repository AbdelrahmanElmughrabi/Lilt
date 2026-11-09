"""Windows file selection without Explorer command-line parsing or quoting."""
import ctypes


def select_file(path):
    shell = ctypes.WinDLL('shell32')
    ole = ctypes.WinDLL('ole32')
    ole.CoInitializeEx.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
    ole.CoInitializeEx.restype = ctypes.c_long
    ole.CoUninitialize.argtypes = []
    ole.CoUninitialize.restype = None
    ole.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole.CoTaskMemFree.restype = None
    shell.SHParseDisplayName.argtypes = [ctypes.c_wchar_p, ctypes.c_void_p,
                                        ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong,
                                        ctypes.POINTER(ctypes.c_ulong)]
    shell.SHParseDisplayName.restype = ctypes.c_long
    shell.SHOpenFolderAndSelectItems.argtypes = [ctypes.c_void_p, ctypes.c_uint,
                                               ctypes.POINTER(ctypes.c_void_p), ctypes.c_ulong]
    shell.SHOpenFolderAndSelectItems.restype = ctypes.c_long
    shell.ILFindLastID.argtypes = [ctypes.c_void_p]
    shell.ILFindLastID.restype = ctypes.c_void_p
    initialized = ole.CoInitializeEx(None, 2)
    # pywebview may already have initialized this thread in a different COM mode.
    if initialized < 0 and initialized != -2147417850:  # RPC_E_CHANGED_MODE
        raise OSError(f'Windows shell initialization failed: {initialized:#x}')
    pidl = ctypes.c_void_p()
    parent = ctypes.c_void_p()
    try:
        result = shell.SHParseDisplayName(str(path), None, ctypes.byref(pidl), 0, None)
        if result < 0:
            raise OSError(f'Windows could not locate the file: {result:#x}')
        result = shell.SHParseDisplayName(str(path.parent), None, ctypes.byref(parent), 0, None)
        if result < 0:
            raise OSError(f'Windows could not locate the folder: {result:#x}')
        child = (ctypes.c_void_p * 1)(shell.ILFindLastID(pidl))
        # Pass an explicit parent and selection, including in media folders.
        # https://learn.microsoft.com/windows/win32/api/shlobj_core/nf-shlobj_core-shopenfolderandselectitems
        result = shell.SHOpenFolderAndSelectItems(parent, 1, child, 0)
        if result < 0:
            raise OSError(f'Windows could not select the file: {result:#x}')
    finally:
        if pidl.value:
            ole.CoTaskMemFree(pidl)
        if parent.value:
            ole.CoTaskMemFree(parent)
        if initialized >= 0:
            ole.CoUninitialize()
