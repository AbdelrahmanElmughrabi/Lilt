# Kokoro synthesis helpers

The chunker, sliding-window, pause, trim and vocabulary files were copied from
Kokoro-ONNX 0.6.1, https://github.com/thewh1teagle/kokoro-onnx, under the MIT
license in LICENSE. The minimal config module is modified to remove all
pronunciation-library configuration. Violilt's inference adapter retains the
upstream synthesis behavior while supplying its own offline English phonemes.

trim.py also contains the librosa contributors' permission notice, retained
verbatim in that file. These copies do not import the upstream pronunciation
package.
