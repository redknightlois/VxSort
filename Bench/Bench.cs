using System;
using System.Drawing;
using System.Runtime.CompilerServices;
using Bench.Utils;
using BenchmarkDotNet.Running;
using Microsoft.VisualBasic.CompilerServices;
using VxSort;
using VxSort.Reference;

namespace Bench
{
    class Program
    {
        static unsafe void Main(string[] args)
        {

            if (true)
            {
                BenchmarkSwitcher
                    .FromAssembly(typeof(Program).Assembly)
                    .Run(args);
            }
            else
            {
                var rnd = new Random(1337);
                var startValue = 16;
                for (int iteration = 0; iteration < 20000; iteration++)
                {
                    startValue += rnd.Next(30);
                    var values = ValuesGenerator.ArrayOfUniqueValues<int>(startValue);
                    for (int i = 0; i < values.Length; i++)
                        values[i] = values[i] % 999;

                    //Console.WriteLine("Values=[{0}]", string.Join(",", values));

                    //Console.WriteLine("---- Reference ----");
                    var array = (int[])values.Clone();
                    VectorizedSort.UnstableSort(array);

                    //Console.WriteLine("---- New ----");
                    var newValues = (int[])values.Clone();
                    fixed (int* valuesPtr = newValues)
                    {
                        var il = valuesPtr;
                        var rl = il + values.Length - 1;

                        Sort.Run(il, rl);
                    }

                    Array.Sort(values);

                    for (int i = 0; i < values.Length; i++)
                    {
                        if (newValues[i] != values[i])
                            Console.WriteLine($"Different at {i}");
                    }

                    if (iteration % 1000 == 0)
                        Console.WriteLine($"Length: {startValue}");
                }
            }

            //var rnd = new Random(1337);

            //var values = ValuesGenerator.ArrayOfUniqueValues<int>(16000000);
            //for (int i = 0; i < values.Length; i++)
            //    values[i] = values[i] % 10000000;

            //for (int iteration = 0; iteration < 30; iteration++)
            //{
            //    var newValues = (int[])values.Clone();
            //    fixed (int* valuesPtr = newValues)
            //    {
            //        var il = valuesPtr;
            //        var rl = il + values.Length - 1;

            //        Sort.Run(il, rl);
            //    }
            //}
        }
    }
}
