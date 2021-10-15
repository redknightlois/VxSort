using System;
using System.Runtime.CompilerServices;
using System.Runtime.InteropServices;
using System.Runtime.Intrinsics;
using System.Runtime.Intrinsics.X86;

namespace VxSort
{
    internal interface IMachineParameters
    {
        int MAX_BITONIC_SORT_VECTORS
        {
            [MethodImpl(MethodImplOptions.AggressiveInlining)]
            get { return 16; }
        }

        int Shift
        {
            [MethodImpl(MethodImplOptions.AggressiveInlining)]
            get { return 0; }
        }

        int Unroll
        {
            [MethodImpl(MethodImplOptions.AggressiveInlining)]
            get { return 16; }
        }

        int N { get; }

        int ELEMENT_ALIGN { get; }

        int MaxInnerUnroll
        {
            [MethodImpl(MethodImplOptions.AggressiveInlining)]
            get { return (MAX_BITONIC_SORT_VECTORS - 3) / 2; }
        }

        int SafeInnerUnroll
        {
            [MethodImpl(MethodImplOptions.AggressiveInlining)]
            get { return MaxInnerUnroll > Unroll ? Unroll : MaxInnerUnroll; }
        }

        int SMALL_SORT_THRESHOLD_ELEMENTS
        {
            [MethodImpl(MethodImplOptions.AggressiveInlining)]
            get { return MAX_BITONIC_SORT_VECTORS * N; }
        }

        // The formula for figuring out how much temporary space we need for partitioning:
        // 2 x the number of slack elements on each side for the purpose of partitioning in unrolled manner +
        // 2 x amount of maximal bytes needed for alignment (32)
        // one more vector's worth of elements since we write with N-way stores from both ends of the temporary area
        // and we must make sure we do not accidentally over-write from left -> right or vice-versa right on that edge...
        // In other words, while we allocated this much temp memory, the actual amount of elements inside said memory
        // is smaller by 8 elements + 1 for each alignment (max alignment is actually N-1, I just round up to N...)
        // This long sense just means that we over-allocate N+2 elements...
        int PARTITION_TMP_SIZE_IN_ELEMENTS
        {
            [MethodImpl(MethodImplOptions.AggressiveInlining)]
            get { return (2 * (Unroll * N) + N + 4 * N); }
        }
    }

    internal unsafe interface IMachineTraits<TParameters>        
        where TParameters : struct, IMachineParameters
    {
        bool supports_compress_writes => false;
        bool supports_packing => false;

        bool can_pack<T>(T right, T left) where T : unmanaged => false;

        void load_vec<TVector>(void* ptr, out TVector vector) where TVector : unmanaged;

        void store_vec<TVector>(void* ptr, in TVector v) where TVector : unmanaged;

        void store_compress_vec<TVector>(void* ptr, in TVector v) where TVector : unmanaged;

        TVector partition_vector<TVector>(in TVector v, uint mask) where TVector : unmanaged;
        TVector broadcast<T, TVector>(T pivot)
            where TVector : unmanaged
            where T : unmanaged;

        uint get_cmpgt_mask<TVector>(in TVector a, in TVector b) where TVector : unmanaged;

        TVector shift_right<TVector>(in TVector v, int i) where TVector : unmanaged;
        TVector shift_left<TVector>(in TVector v, int i) where TVector : unmanaged;

        TVector add<TVector>(in TVector a, in TVector b) where TVector : unmanaged;
        TVector sub<TVector>(in TVector a, in TVector b) where TVector : unmanaged;

        TVector pack_ordered<TVector>(in TVector a, in TVector b) where TVector : unmanaged;
        TVector pack_unordered<TVector>(in TVector a, in TVector b) where TVector : unmanaged;

        void unpack_ordered<TVector>(in TVector p, ref TVector u1, ref TVector u2) where TVector : unmanaged;

        T shift_n_sub<T>(T v, T sub) where T : unmanaged
        {
            throw new NotImplementedException();
        }
        T unshift_and_add<T>(int from, T add)
        {
            throw new NotImplementedException();
        }

        int popcnt(uint mask);
    }
}
