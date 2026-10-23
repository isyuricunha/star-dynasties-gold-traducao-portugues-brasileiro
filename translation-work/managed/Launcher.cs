using System;
using System.IO;
using System.Reflection;

public static class Launcher
{
    public static int Main(string[] args)
    {
        try
        {
            string location = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            // Load the private dependency before the CLR can JIT any Cecil-using code.
            var dependency = Assembly.LoadFrom(Path.GetFullPath(Path.Combine(location, "../vendor/mono-cecil-0.11.6/Mono.Cecil.dll")));
            AppDomain.CurrentDomain.AssemblyResolve += delegate(object sender, ResolveEventArgs request)
            {
                return new AssemblyName(request.Name).Name == "Mono.Cecil" ? dependency : null;
            };
            var entry = Assembly.GetExecutingAssembly().GetType("GrammarTool", true)
                .GetMethod("Main", BindingFlags.Public | BindingFlags.Static);
            return (int)entry.Invoke(null, new object[] { args });
        }
        catch (Exception error)
        {
            while (error is TargetInvocationException && error.InnerException != null) error = error.InnerException;
            Console.Error.WriteLine("ERROR: " + error.GetType().Name + ": " + error.Message);
            return 1;
        }
    }
}
