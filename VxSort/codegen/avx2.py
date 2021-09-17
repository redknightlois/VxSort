##
## Licensed to the .NET Foundation under one or more agreements.
## The .NET Foundation licenses this file to you under the MIT license.
##

import os
from datetime import datetime

from utils import native_size_map, next_power_of_2
from bitonic_isa import BitonicISA


class AVX2BitonicISA(BitonicISA):
    def __init__(self, type):
        self.vector_size_in_bytes = 32

        self.type = type

        self.bitonic_size_map = {}

        for t, s in native_size_map.items():
            self.bitonic_size_map[t] = int(self.vector_size_in_bytes / s)

        self.bitonic_type_map = {
            "int": "Int32",
            "uint": "Int32",
            "float": "Int32",
            "long": "Int64",
            "ulong": "Int64",
            "double": "Int64",
        }

    def max_bitonic_sort_vectors(self):
        return 16

    def vector_size(self):
        return self.bitonic_size_map[self.type]

    def vector_type(self):
        return "V"

    @classmethod
    def supported_types(cls):
        return native_size_map.keys()

    def i2d(self, v):
        t = self.type
        if t == "double":
            return v
        elif t == "float":
            return f"s2d({v})"
        return f"i2d({v})"

    def i2s(self, v):
        t = self.type
        if t == "double":
            raise Exception("Incorrect Type")
        elif t == "float":
            return f"i2s({v})"
        return v

    def d2i(self, v):
        t = self.type
        if t == "double":
            return v
        elif t == "float":
            return f"d2s({v})"
        return f"d2i<{t}>({v})"

    def s2i(self, v):
        t = self.type
        if t == "double":
            raise Exception("Incorrect Type")
        elif t == "float":
            return f"s2i<int>({v})"
        return v

    def generate_param_list(self, start, numParams):
        return str.join(", ", list(map(lambda p: f"ref d{p:02d}", range(start, start + numParams))))

    def generate_param_def_list(self, numParams):
        return str.join(", ", list(map(lambda p: f"ref {self.vector_type()} d{p:02d}", range(1, numParams + 1))))

    def generate_shuffle_X1(self, v):
        size = self.vector_size()
        if size == 8:
            return self.i2s(f"Shuffle({self.s2i(v)}, 0xB1)")
        elif size == 4:
            return self.d2i(f"Shuffle({self.i2d(v)}, {self.i2d(v)}, 0x5)")

    def generate_shuffle_X2(self, v):
        size = self.vector_size()
        if size == 8:
            return self.i2s(f"Shuffle({self.s2i(v)}, 0x4E)")
        elif size == 4:
            return self.d2i(f"Permute4x64({self.i2d(v)}, 0x4E)")

    def generate_shuffle_XR(self, v):
        size = self.vector_size()
        if size == 8:
            return self.i2s(f"Shuffle({self.s2i(v)}, 0x1B)")
        elif size == 4:
            return self.d2i(f"Permute4x64({self.i2d(v)}, 0x1B)")

    def generate_blend_B1(self, v1, v2, ascending):
        size = self.vector_size()
        if size == 8:
            if ascending:
                return self.i2s(f"Blend({self.s2i(v1)}, {self.s2i(v2)}, 0xAA)")
            else:
                return self.i2s(f"Blend({self.s2i(v2)}, {self.s2i(v1)}, 0xAA)")
        elif size == 4:
            if ascending:
                return self.d2i(f"Blend({self.i2d(v1)}, {self.i2d(v2)}, 0xA)")
            else:
                return self.d2i(f"Blend({self.i2d(v2)}, {self.i2d(v1)}, 0xA)")

    def generate_blend_B2(self, v1, v2, ascending):
        size = self.vector_size()
        if size == 8:
            if ascending:
                return self.i2s(f"Blend({self.s2i(v1)}, {self.s2i(v2)}, 0xCC)")
            else:
                return self.i2s(f"Blend({self.s2i(v2)}, {self.s2i(v1)}, 0xCC)")
        elif size == 4:
            if ascending:
                return self.d2i(f"Blend({self.i2d(v1)}, {self.i2d(v2)}, 0xC)")
            else:
                return self.d2i(f"Blend({self.i2d(v2)}, {self.i2d(v1)}, 0xC)")

    def generate_blend_B4(self, v1, v2, ascending):
        size = self.vector_size()
        if size == 8:
            if ascending:
                return self.i2s(f"Blend({self.s2i(v1)}, {self.s2i(v2)}, 0xF0)")
            else:
                return self.i2s(f"Blend({self.s2i(v2)}, {self.s2i(v1)}, 0xF0)")
        elif size == 4:
            raise Exception("Incorrect Size")

    def generate_cross(self, v):
        size = self.vector_size()
        if size == 8:
            return self.d2i(f"Permute4x64({self.i2d(v)}, 0x4E)")
        elif size == 4:
            raise Exception("Incorrect Size")

    def generate_reverse(self, v):
        size = self.vector_size()
        if size == 8:
            v = f"Shuffle({self.s2i(v)}, 0x1B)"
            return self.d2i(f"Permute4x64(i2d({v}), 0x4E)")
        elif size == 4:
            return self.d2i(f"Permute4x64({self.i2d(v)}, 0x1B)")

    def crappity_crap_crap(self, v1, v2):
        t = self.type
        if t == "long":
            return f"cmp = CompareGreaterThan({v1}, {v2});"
        elif t == "ulong":
            return f"cmp = CompareGreaterThan(Xor(topBit, {v1}).AsInt64(), Xor(topBit, {v2}).AsInt64()).AsUInt64();"

        return ""

    def generate_min(self, v1, v2):
        t = self.type
        if t == "int":
            return f"Min({v1}, {v2})"
        elif t == "uint":
            return f"Min({v1}, {v2})"
        elif t == "float":
            return f"Min({v1}, {v2})"
        elif t == "long":
            return self.d2i(f"BlendVariable({self.i2d(v1)}, {self.i2d(v2)}, i2d(cmp))")
        elif t == "ulong":
            return self.d2i(f"BlendVariable({self.i2d(v1)}, {self.i2d(v2)}, i2d(cmp))")
        elif t == "double":
            return f"Min({v1}, {v2})"

    def generate_max(self, v1, v2):
        t = self.type
        if t == "int":
            return f"Max({v1}, {v2})"
        elif t == "uint":
            return f"Max({v1}, {v2})"
        elif t == "float":
            return f"Max({v1}, {v2})"
        elif t == "long":
            return self.d2i(f"BlendVariable({self.i2d(v2)}, {self.i2d(v1)}, i2d(cmp))")
        elif t == "ulong":
            return self.d2i(f"BlendVariable({self.i2d(v2)}, {self.i2d(v1)}, i2d(cmp))")
        elif t == "double":
            return f"Max({v1}, {v2})"

    def get_load_intrinsic(self, v, offset):
        t = self.type
        if t == "double":
            return f"LoadVector256({v} + V.Count * {offset})"
        if t == "float":
            return f"LoadVector256({v} + V.Count * {offset})"
        return f"LoadVector256({v} + V.Count * {offset})"

    def get_mask_load_intrinsic(self, v, offset, mask):
        t = self.type

        if self.vector_size() == 4:
            max_value = f"AndNot({mask}, Vector256.Create({t}.MaxValue))"
        elif self.vector_size() == 8:
            max_value = f"AndNot({mask}, Vector256.Create({t}.MaxValue))"

        if t == "double":
            max_value = f"AndNot(mask, Vector256.Create({t}.MaxValue))"
            load = f"MaskLoad({v} +  V.Count * {offset}, {mask})"
            return f"Or({load}, {max_value})"
        if t == "float":
            max_value = f"AndNot(mask, Vector256.Create({t}.MaxValue))"
            load = f"MaskLoad({v} +  V.Count * {offset}, {mask})"
            return f"Or({load}, {max_value})"

        load = f"MaskLoad({v} + V.Count * {offset}, {mask})"
        return f"Or({load}, {max_value})"

    def get_store_intrinsic(self, ptr, offset, value):
        t = self.type
        if t == "double":
            return f"Store(({t} *) ({ptr} +  V.Count * {offset}), {value})"
        if t == "float":
            return f"Store(({t} *) ({ptr} +  V.Count * {offset}), {value})"
        return f"Store({ptr} + V.Count * {offset}, {value})"

    def get_mask_store_intrinsic(self, ptr, offset, value, mask):
        t = self.type

        if t == "double":
            return f"MaskStore({ptr} +  V.Count * {offset}, {mask}, {value})"
        if t == "float":
            return f"MaskStore({ptr} +  V.Count * {offset}, {mask}, {value})"

        return f"MaskStore({ptr} +  V.Count * {offset}, {mask}, {value})"

    def autogenerated_blabber(self):
        return f"""/////////////////////////////////////////////////////////////////////////////
////
// This file was auto-generated by a tool at {datetime.now().strftime("%F %H:%M:%S")}
//
// It is recommended you DO NOT directly edit this file but instead edit
// the code-generator that generated this source file instead.
/////////////////////////////////////////////////////////////////////////////"""

    def generate_prologue(self, f):
        t = self.type
        s = f"""{self.autogenerated_blabber()}

using System;
using System.Diagnostics;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using static System.Runtime.Intrinsics.X86.Avx;
using static System.Runtime.Intrinsics.X86.Avx2;
using static System.Runtime.Intrinsics.X86.Sse2;
using static System.Runtime.Intrinsics.X86.Sse41;
using static System.Runtime.Intrinsics.X86.Sse42;

namespace VxSort
{{
    using V = Vector256<{self.type}>;
    static unsafe partial class BitonicSortAvx<T>
    {{
"""
        print(s, file=f)

    def generate_epilogue(self, f):
        s = f"""
    }};
}}
    """
        print(s, file=f)

    def generate_1v_basic_sorters(self, f, ascending):
        g = self
        type = self.type
        maybe_cmp = lambda: ", cmp" if (type == "long" or type == "ulong") else ""
        maybe_topbit = lambda: f"\n        {g.vector_type()} topBit = Vector256.Create(1UL << 63);" if (type == "ulong") else ""
        suffix = "ascending" if ascending else "descending"

        s = f"""
        [MethodImpl(MethodImplOptions.AggressiveInlining | MethodImplOptions.AggressiveOptimization)]
        public static void sort_01v_{suffix}({g.generate_param_def_list(1)}) {{
            {g.vector_type()}  min, max, s{maybe_cmp()};{maybe_topbit()}

            s = {g.generate_shuffle_X1("d01")};
            {g.crappity_crap_crap("s", "d01")}
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B1("min", "max", ascending)};

            s = {g.generate_shuffle_XR("d01")};
            {g.crappity_crap_crap("s", "d01")}
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B2("min", "max", ascending)};

            s = {g.generate_shuffle_X1("d01")};
            {g.crappity_crap_crap("s", "d01")}
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B1("min", "max", ascending)};"""

        print(s, file=f)

        if g.vector_size() == 8:
            s = f"""
            s = {g.generate_reverse("d01")};
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B4("min", "max", ascending)};

            s = {g.generate_shuffle_X2("d01")};
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B2("min", "max", ascending)};

            s = {g.generate_shuffle_X1("d01")};
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B1("min", "max", ascending)};"""
            print(s, file=f)
        print("}", file=f)



    def generate_1v_merge_sorters(self, f, ascending: bool):
        g = self
        type = self.type
        maybe_cmp = lambda: ", cmp" if (type == "long" or type == "ulong") else ""
        maybe_topbit = lambda: f"\n        {g.vector_type()} topBit = Vector256.Create(1UL << 63);" if (type == "ulong") else ""

        suffix = "ascending" if ascending else "descending"

        s = f"""
        [MethodImpl(MethodImplOptions.AggressiveInlining | MethodImplOptions.AggressiveOptimization)]
        public static void sort_01v_merge_{suffix}({g.generate_param_def_list(1)}) {{
            {g.vector_type()}  min, max, s{maybe_cmp()};{maybe_topbit()}"""
        print(s, file=f)

        if g.vector_size() == 8:
            s = f"""
            s = {g.generate_cross("d01")};
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B4("min", "max", ascending)};"""
            print(s, file=f)

        s = f"""
            s = {g.generate_shuffle_X2("d01")};
            {g.crappity_crap_crap("s", "d01")}
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B2("min", "max", ascending)};

            s = {g.generate_shuffle_X1("d01")};
            {g.crappity_crap_crap("s", "d01")}
            min = {g.generate_min("s", "d01")};
            max = {g.generate_max("s", "d01")};
            d01 = {g.generate_blend_B1("min", "max", ascending)};"""

        print(s, file=f)
        print("    }", file=f)

    def generate_compounded_sorter(self, f, width, ascending, inline):
        type = self.type
        g = self
        maybe_cmp = lambda: ", cmp" if (type == "long" or type == "ulong") else ""
        maybe_topbit = lambda: f"\n        {g.vector_type()} topBit = Vector256.Create(1UL << 63);" if (type == "ulong") else ""

        w1 = int(next_power_of_2(width) / 2)
        w2 = int(width - w1)

        suffix = "ascending" if ascending else "descending"
        rev_suffix = "descending" if ascending else "ascending"

        inl = "AggressiveInlining" if inline else "NoInlining"

        s = f"""
    [MethodImpl(MethodImplOptions.{inl} | MethodImplOptions.AggressiveOptimization)]        
    private static void sort_{width:02d}v_{suffix}({g.generate_param_def_list(width)}) {{
        {g.vector_type()}  tmp{maybe_cmp()};{maybe_topbit()}

        sort_{w1:02d}v_{suffix}({g.generate_param_list(1, w1)});
        sort_{w2:02d}v_{rev_suffix}({g.generate_param_list(w1 + 1, w2)});"""

        print(s, file=f)

        for r in range(w1 + 1, width + 1):
            x = w1 + 1 - (r - w1)
            s = f"""
            tmp = d{r:02d};
            {g.crappity_crap_crap(f"d{x:02d}", f"d{r:02d}")}
            d{r:02d} = {g.generate_max(f"d{x:02d}", f"d{r:02d}")};
            d{x:02d} = {g.generate_min(f"d{x:02d}", "tmp")};"""
            print(s, file=f)

        s = f"""
        sort_{w1:02d}v_merge_{suffix}({g.generate_param_list(1, w1)});
        sort_{w2:02d}v_merge_{suffix}({g.generate_param_list(w1 + 1, w2)});"""
        print(s, file=f)
        print("    }", file=f)


    def generate_compounded_merger(self, f, width, ascending, inline):
        type = self.type
        g = self
        maybe_cmp = lambda: ", cmp" if (type == "long" or type == "ulong") else ""
        maybe_topbit = lambda: f"\n        {g.vector_type()} topBit = Vector256.Create(1UL << 63);" if (type == "ulong") else ""

        w1 = int(next_power_of_2(width) / 2)
        w2 = int(width - w1)

        suffix = "ascending" if ascending else "descending"
        rev_suffix = "descending" if ascending else "ascending"

        inl = "AggressiveInlining" if inline else "NoInlining"

        s = f"""
    [MethodImpl(MethodImplOptions.{inl} | MethodImplOptions.AggressiveOptimization)]        
    private static void sort_{width:02d}v_merge_{suffix}({g.generate_param_def_list(width)}) {{
        {g.vector_type()}  tmp{maybe_cmp()};{maybe_topbit()}"""
        print(s, file=f)

        for r in range(w1 + 1, width + 1):
            x = r - w1
            s = f"""
            tmp = d{x:02d};
            {g.crappity_crap_crap(f"d{r:02d}", f"d{x:02d}")}
            d{x:02d} = {g.generate_min(f"d{r:02d}", f"d{x:02d}")};
            {g.crappity_crap_crap(f"d{r:02d}", "tmp")}
            d{r:02d} = {g.generate_max(f"d{r:02d}", "tmp")};"""
            print(s, file=f)

        s = f"""
        sort_{w1:02d}v_merge_{suffix}({g.generate_param_list(1, w1)});
        sort_{w2:02d}v_merge_{suffix}({g.generate_param_list(w1 + 1, w2)});"""
        print(s, file=f)
        print("    }", file=f)

    def generate_entry_points(self, f):
        type = self.type
        g = self
        for m in range(1, g.max_bitonic_sort_vectors() + 1):
            mask = f"""ConvertToVector256{self.bitonic_type_map[type]}(LoadVector128((sbyte*)Unsafe.AsPointer(ref MemoryMarshal.GetReference(mask_table_{self.vector_size()})) + remainder * V.Count))"""
            if type == "double":
                mask = f"""i2d({mask})"""
            elif type == "float":
                mask = f"""i2s({mask})"""
            elif type == 'uint':
                mask = f"""{mask}.AsUInt32()"""
            elif type == 'ulong':
                mask = f"""{mask}.AsUInt64()"""

            s = f"""
        [MethodImpl(MethodImplOptions.NoInlining | MethodImplOptions.AggressiveOptimization)]
        private static void sort_{m:02d}v_alt({type} *ptr, int remainder) 
        {{        
            var mask = {mask};
"""
            print(s, file=f)

            for l in range(0, m-1):
                s = f"      {g.vector_type()} d{l + 1:02d} = {g.get_load_intrinsic('ptr', l)};"
                print(s, file=f)

            s = f"      {g.vector_type()} d{m:02d} = {g.get_mask_load_intrinsic('ptr', m - 1, 'mask')};"
            print(s, file=f)

            s = f"      sort_{m:02d}v_ascending({g.generate_param_list(1, m)});"
            print(s, file=f)

            for l in range(0, m-1):
                s = f"      {g.get_store_intrinsic('ptr', l, f'd{l + 1:02d}')};"
                print(s, file=f)

            s = f"      {g.get_mask_store_intrinsic('ptr', m - 1, f'd{m:02d}', 'mask')};"
            print(s, file=f)

            print("     }", file=f)

    def generate_master_entry_point(self, f_header):

        t = self.type
        s = f"""
    [MethodImpl(MethodImplOptions.AggressiveInlining | MethodImplOptions.AggressiveOptimization)]
    public static void Sort({t}* ptr, int length)"""
        print(s, file=f_header)

        s = f"""    {{
        var fullvlength = length / V.Count;
        var remainder = (int) (length - fullvlength * V.Count);
        var v = fullvlength + ((remainder > 0) ? 1 : 0);
        
        switch (v) {{"""
        print(s, file=f_header)

        for m in range(1, self.max_bitonic_sort_vectors() + 1):
            s = f"        case {m}: sort_{m:02d}v_alt(ptr, remainder); break;"
            print(s, file=f_header)

        print("         }", file=f_header)
        print("     }", file=f_header)

        pass
