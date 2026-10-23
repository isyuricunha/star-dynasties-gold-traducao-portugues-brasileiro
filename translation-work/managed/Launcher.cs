using System;
using System.IO;
using System.Reflection;

public static class Launcher
{
    public static int Main(string[] args)
    {
        AppDomain.CurrentDomain.AssemblyResolve += delegate(object sender, ResolveEventArgs e)
        {
            if (new AssemblyName(e.Name).Name != "Mono.Cecil") return null;
            string location = Path.GetDirectoryName(Assembly.GetExecutingAssembly().Location);
            return Assembly.LoadFrom(Path.GetFullPath(Path.Combine(location, "../vendor/mono-cecil-0.11.6/Mono.Cecil.dll")));
        };
        return GrammarTool.Main(args);
    }
}
