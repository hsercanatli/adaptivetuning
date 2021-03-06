# This algorithm is a modified version of the algorithm originally written
# by Martin C. Doege
# The algorithm is hosted at:
# https://github.com/mdoege/PySynth/blob/master/pysynth_s.py
# We adapted the code from v1.1.2, commit 7a704e6 on Jul 22, 2012.
# The original code is licenced under the GPL.

import wave
import numpy as np
import json
from math import cos, pi, log, floor, ceil
try:
    from cStringIO import StringIO
except ImportError:
    from io import StringIO


def make_wav(score, bpm, transpose=0, pause=0.0, repeat=0, fn="",
             silent=False, verbose=False):

    # wave settings
    if not fn:
        fn = StringIO()

    f = wave.open(fn, 'w')

    f.setnchannels(1)
    f.setsampwidth(2)
    f.setframerate(44100)
    f.setcomptype('NONE', 'Not Compressed')

    bpm_fac = 30. / bpm

    def length(l):
        return 88200. / l * bpm_fac

    def waves2(hz, l):
        a = 44100. / hz
        b = float(l) / 44100. * hz
        return [a, round(b)]

    def render2(a, b, vol, pos, endamp=0.25, sm=10):
        b2 = (1. - pause) * b
        l = waves2(a, b2)
        q = int(l[0] * l[1])

        lf = log(a)
        t = (lf - 3.) / (8.5 - 3.)
        volfac = 1. + .8 * t * cos(pi / 5.3 * (lf - 3.))
        snd_len = int((10. - lf) * q)
        if lf < 4:
            snd_len *= 2

        kp_len = int(l[0])
        kps1 = np.zeros(snd_len)
        kps2 = np.zeros(snd_len)
        kps1[:kp_len] = np.random.normal(size=kp_len)

        for t in range(kp_len):
            kps2[t] = kps1[t:t + sm].mean()
        delt = float(l[0])
        li = int(floor(delt))
        hi = int(ceil(delt))
        ifac = delt % 1
        delt2 = delt * (floor(delt) - 1) / floor(delt)
        ifac2 = delt2 % 1
        falloff = (4. / lf * endamp) ** (1. / l[1])
        for t in range(hi, snd_len):
            v1 = ifac * kps2[t - hi] + (1. - ifac) * kps2[t - li]
            v2 = ifac2 * kps2[t - hi + 1] + (1. - ifac2) * kps2[t - li + 1]
            kps2[t] += .5 * (v1 + v2) * falloff

        data[pos:pos + snd_len] += kps2[0:snd_len] * vol * volfac

    ex_pos = 0.
    t_len = 0

    time_stamp = 0.
    symbtr_map = []

    for x in score:
        # ornamentations are ignored
        if int(x[9]) != 0 and int(x[10]) != 0:
            if int(x[10]) * int(x[9]) < 0:
                t_len += length(-2. * (float(x[10]) * float(x[9])) / 3.)
            else:
                t_len += length(float(x[10]) / float(x[9]))

    data = np.zeros(int((repeat + 1) * t_len + 20. * 44100.))

    for rp in range(repeat + 1):
        for nn, x in enumerate(score):
            if verbose and not nn % 10 and not silent:
                print("[%u/%u]\t" % (nn + 1, len(score)))

            # and int(x[4]) != 0 and int(x[5]) != 0:
            if x[0] != u'Rr' and int(x[9]) != 0 and int(x[10]) != 0:

                vol = 1.
                a = float(x[11])  # frequency
                a *= 2 ** transpose

                b = length(float(x[10]) / float(x[9]))

                render2(a, b, vol, int(ex_pos))
                ex_pos += b

                symbtr_map.append((x[0], x[7], time_stamp))
                time_stamp += b / 44100.

            if x[0] == u'Rr':
                b = length(float(x[10]) / float(x[9]))
                ex_pos += b

                symbtr_map.append((x[0], x[7], time_stamp))
                time_stamp += b / 44100.

    if not silent and verbose:
        print("Writing wav to ", fn)

    data /= data.max() * 2.
    out_len = int(2. * 44100. + ex_pos + .5)
    data2 = np.zeros(out_len, np.short)
    data2[:] = 32000. * data[:out_len]
    f.writeframes(data2.tostring())
    f.close()

    try:
        return fn.getvalue(), symbtr_map
    except:
        return fn, symbtr_map
