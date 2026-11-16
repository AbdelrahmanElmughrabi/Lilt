# num2words source and compatible library replacement

Violilt uses num2words 0.5.14, licensed LGPL-2.1-or-later, through its external
Python files. The selected compliance arrangement uses LGPL 2.1 section 6(b).
The matching complete source is `sources/num2words-0.5.14.tar.gz`; its hash is in
`sources/source-manifest.json`. The full license is `native/LGPL-2.1.txt`, with
library-specific notices in `python/num2words-0.5.14/` and the source archive.

For the current classic folder/EXE distribution:

1. Close Violilt fully. Keep the original application folder as a backup. Copy
   the whole folder containing `Violilt.exe`, `_internal`, `models`, `gpu-runtime`
   and `third-party` into a new directory that you can write to. Preserve all
   accompanying files and notices. The per-user test install normally lives at
   `%LOCALAPPDATA%\Programs\VioliltTest`.
2. Extract the accompanying num2words archive with a tar-compatible reader.
   Make an interface-compatible modification, retaining its license and notices.
   Replace the corresponding `.py` files under the copied application's
   `_internal/num2words/`. Keep its package interface and metadata compatible.
   The library is outside the executable's frozen archive; no app rebuild is
   required. Do not change files while the application is running.
3. Start the copied `Violilt.exe`. To try it with a fresh library without touching
   existing documents/recordings, start it with `--data-dir` followed by the quoted
   path to a new writable library folder. Use a synthetic sentence containing a
   number. The replacement must implement the same required num2words interfaces.
4. Restart after each library change. Violilt fingerprints number-reading source
   for cache identity and refuses code changes within an already running
   pronunciation session. A changed compatible library therefore gets a new
   pronunciation identity rather than silently reusing old generated content.
   Restore the backup library files and restart to return to the original code.

Applicable application terms must permit modification of the combined work for
your own use and reverse engineering to debug those modifications as required
by LGPL section 6. This permission is not confined to library-file edits. Source
access and those permissions do not depend on a paid source request or hosted
source offer. Independent application files need not be publicly redistributed
under this shared-library route.

This arrangement does not authorize bypassing model/GPU integrity checks,
package signatures or WindowsApps permissions. A protected Store/MSIX release
must supply its own equivalent usable writable companion or another fully
implemented section 6 route. These classic-EXE instructions alone do not certify
that future distribution. SoundFile/libsndfile runtime code is absent from the
current payload; retained historical notices/archives do not clear old payloads.
