using System;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Runtime.Intrinsics;
using V = System.Runtime.Intrinsics.Vector256<int>;

namespace VxSort
{
    // We will use type erasure to ensure that we can create specific variants of this same algorithm. 
    public unsafe static class Sort
    {
        internal const ulong ALIGN = 32;
        internal const ulong ALIGN_MASK = ALIGN - 1;

        internal const long REALIGN_LEFT = 0x666;
        internal const long REALIGN_RIGHT = 0x66600000000;
        internal const long REALIGN_BOTH = REALIGN_LEFT | REALIGN_RIGHT;

        static int FloorLog2PlusOne(uint n)
        {
            var result = 0;
            while (n >= 1)
            {
                result++;
                n /= 2;
            }
            return result;
        }

        public static void Run<T>([NotNull] T[] array)
            where T : unmanaged
        {
            if (array == null)
                throw new ArgumentNullException(nameof(array));

            fixed ( T* arrayPtr = array )
            {
                T* left = arrayPtr;
                T* right = arrayPtr + array.Length;
                Run(left, right);
            }
        }

        [SkipLocalsInit]
        public static void Run<T>(T* left, T* right)
            where T : unmanaged
        {
            if (typeof(T) == typeof(int))
            {
                int* il = (int*)left;
                int* ir = (int*)right;

                uint length = (uint)(ir - il);

                int N = Vector256<int>.Count;
                int SMALL_SORT_THRESHOLD_ELEMENTS = 20 * N;

                if (length < SMALL_SORT_THRESHOLD_ELEMENTS)
                    BitonicSort.Sort(il, (int)length);

                var depthLimit = 2 * FloorLog2PlusOne(length);
                //var sorter = new VectorizedSort<Avx2InstructionSet<AvxInt32MachineParameters>, AvxInt32MachineParameters>(il, ir);

                var sorter = new Avx2VectorizedSort(il, ir);
                sorter.sort(il, ir, 0, 0, REALIGN_BOTH, depthLimit);
                return;
            }
            if (typeof(T) == typeof(long))
            {
                long* il = (long*)left;
                long* ir = (long*)right;

                uint length = (uint)(ir - il);
                if (length < 16)
                    throw new NotSupportedException();

                var depthLimit = 2 * FloorLog2PlusOne(length);
                //var sorter = new VectorizedSort<Avx2InstructionSet<AvxInt64MachineParameters>, AvxInt64MachineParameters>(il, ir);
                //sorter.sort(il, ir, 0, 0, REALIGN_BOTH, depthLimit);
                return;
            }
            throw new NotSupportedException();
        }
    }
}
