// Metadata-only assembly editing. Game code is executed only by the separate test harness.
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Security.Cryptography;
using System.Text;
using System.Web.Script.Serialization;
using Mono.Cecil;
using Mono.Cecil.Cil;

public static class GrammarTool
{
    const string Parser = "Pawley.StarDynasties.Engine.Text.Parsing.ParsingHelper";
    const string Kin = "Pawley.StarDynasties.Engine.Simulation.Kinship.KinRelationshipVerbalizer_eng";
    const string Helper = "__PtBrFormatReference";
    const string CharHelper = "__PtBrCharacterVerb";
    static readonly JavaScriptSerializer Json = new JavaScriptSerializer { MaxJsonLength = Int32.MaxValue, RecursionLimit = 200 };
    public sealed class Unit
    {
        public string key;
        public string method;
        public string role;
        public string operation;
        public string EN;
        public bool empty_allowed;
        public bool argument;
        public int slot;
    }
    sealed class Plan
    {
        public MethodDefinition Method;
        public List<Unit> Units = new List<Unit>();
        public List<Instruction> Strings;
        public string Kind;
    }
    static string Hash(string text)
    {
        using (var sha = SHA256.Create()) return BitConverter.ToString(sha.ComputeHash(Encoding.UTF8.GetBytes(text))).Replace("-", "").ToLowerInvariant();
    }
    static IEnumerable<TypeDefinition> Types(ModuleDefinition module)
    {
        foreach (var t in module.Types) foreach (var x in Types(t)) yield return x;
    }
    static IEnumerable<TypeDefinition> Types(TypeDefinition type)
    {
        yield return type;
        foreach (var t in type.NestedTypes) foreach (var x in Types(t)) yield return x;
    }
    static bool Patched(ModuleDefinition module)
    {
        return module.GetType(Parser).Methods.Any(m => m.Name == Helper);
    }
    static void Add(Plan plan, int slot, string role, string value, bool argument, bool empty)
    {
        plan.Units.Add(new Unit { key = plan.Method.FullName + "#" + role, method = plan.Method.FullName,
            role = role, operation = plan.Kind, EN = value, argument = argument, empty_allowed = empty, slot = slot });
    }
    static List<Plan> Plans(ModuleDefinition module)
    {
        var parser = module.GetType(Parser);
        if (parser == null || module.GetType(Kin) == null) throw new InvalidDataException("Unsupported engine: grammar types missing");
        var output = new List<Plan>();
        bool patched = Patched(module);
        string[] roles = { "player", "male", "female", "unknown" };
        foreach (var method in parser.Methods)
        {
            if (!method.HasBody) continue;
            var p = new Plan { Method = method, Strings = method.Body.Instructions.Where(i => i.OpCode == OpCodes.Ldstr).ToList(), Kind = "literal" };
            var s = p.Strings.Select(i => (string)i.Operand).ToArray();
            if (new[] { "he", "He", "him", "Him", "his", "His" }.Contains(method.Name))
            {
                if (s.Length != 4) throw new InvalidDataException("Unexpected pronoun method shape");
                for (int i = 0; i < 4; i++) Add(p, i, roles[i], s[i], false, false);
            }
            else if (method.Name == "himself")
            {
                if (s.Length != 5 || s[4] != "[Null parameter]") throw new InvalidDataException("Unexpected reflexive shape");
                for (int i = 0; i < 4; i++) Add(p, i, roles[i], s[i], false, false);
            }
            else if (method.Name == "DInternal" && method.Parameters.Count == 3)
            {
                if (s.Length != 5 || s[0] != "[Null parameter]") throw new InvalidDataException("Unexpected reference shape");
                string[] order = { "player", "unknown", "female", "male" };
                for (int i = 1; i < 5; i++) Add(p, i, order[i - 1], s[i], false, false);
            }
            else if (method.Name == "listAsSentence")
            {
                if (s.Length != 5 || s[0] != "[Null parameter]" || s[1] != "und") throw new InvalidDataException("Unexpected list shape");
                Add(p, 2, "english-conjunction", s[2], false, false);
            }
            else if (method.Name == "s" || method.Name == "es")
            {
                if (s.Length != 2) throw new InvalidDataException("Unexpected suffix shape");
                Add(p, 0, "player-suffix", s[0], false, true);
                Add(p, 1, "other-suffix", s[1], false, true);
            }
            else if (method.Name == "d_s" || method.Name == "dp_s")
            {
                if (s.Length != 3 || s[0] != "[Null parameter]") throw new InvalidDataException("Unexpected possessive shape");
                p.Kind = "possessive";
                Add(p, 1, "player", s[1], false, false);
                Add(p, 2, "reference-template", patched ? s[2] : "{0}" + s[2], true, false);
            }
            else if (new[] { "hehas", "Hehas", "heis", "Heis", "hewas", "Hewas" }.Contains(method.Name))
            {
                p.Kind = "pronoun-phrase";
                if (patched)
                {
                    if (s.Length != 5 || s[0] != "[Null parameter]") throw new InvalidDataException("Unexpected patched phrase shape");
                    for (int i = 0; i < 4; i++) Add(p, i + 1, roles[i], s[i + 1], false, false);
                }
                else
                {
                    if (s.Length != 6) throw new InvalidDataException("Unexpected compound phrase shape");
                    for (int i = 0; i < 4; i++) Add(p, i, roles[i], s[i] + s[(i == 0 || i == 3) ? 4 : 5], false, false);
                }
            }
            else if (new[] { "dhas", "Dhas", "dis", "Dis", "dwas", "Dwas" }.Contains(method.Name))
            {
                p.Kind = "character-verb";
                if (s.Length != (patched ? 3 : 2)) throw new InvalidDataException("Unexpected character verb shape");
                Add(p, 0, "player-template", patched ? s[0] : "{0}" + s[0], true, false);
                Add(p, 1, "visible-template", patched ? s[1] : "{0}" + s[1], true, false);
                Add(p, 2, "unknown-template", patched ? s[2] : "{0}" + s[1], true, false);
            }
            if (p.Units.Count > 0) output.Add(p);
        }
        foreach (var method in module.GetType(Kin).Methods)
        {
            if (!method.HasBody) continue;
            var p = new Plan { Method = method, Strings = method.Body.Instructions.Where(i => i.OpCode == OpCodes.Ldstr).ToList(), Kind = "literal" };
            var s = p.Strings.Select(i => (string)i.Operand).ToArray();
            if ((method.Name == "VerbaliseRelationship" || method.Name == "VerbaliseGeneticRelationship") && method.Parameters.Count == 3)
            {
                if (s.Length != 7 || s[6] != "Kinship.Unrelated") throw new InvalidDataException("Unexpected kinship fallback shape");
                string[] order = { "none", "self", "player", "male", "female", "unknown" };
                for (int i = 0; i < 6; i++) Add(p, i, "distant-" + order[i], s[i], false, false);
            }
            else if (method.Name == "MapTerm")
            {
                if (s.Length != 5) throw new InvalidDataException("Unexpected kinship determiner shape");
                p.Kind = "kinship-template";
                string[] order = { "self", "player", "male", "female", "unknown" };
                for (int i = 0; i < 5; i++) Add(p, i, order[i], patched ? s[i] : s[i] + "{0}", true, false);
            }
            if (p.Units.Count > 0) output.Add(p);
        }
        if (output.Sum(p => p.Units.Count) != 100) throw new InvalidDataException("Expected exactly 100 mapped grammar units");
        return output.OrderBy(p => p.Method.FullName, StringComparer.Ordinal).ToList();
    }
    static string Operand(object operand, MethodDefinition method, bool maskStrings)
    {
        if (operand == null) return "";
        var instruction = operand as Instruction;
        if (instruction != null) return "@" + method.Body.Instructions.IndexOf(instruction);
        var branches = operand as Instruction[];
        if (branches != null) return String.Join(",", branches.Select(i => "@" + method.Body.Instructions.IndexOf(i)).ToArray());
        if (operand is string) return maskStrings ? "<string>" : Json.Serialize(operand);
        return Convert.ToString(operand, System.Globalization.CultureInfo.InvariantCulture);
    }
    static string Body(MethodDefinition method, bool maskStrings)
    {
        if (!method.HasBody) return "no-body";
        return String.Join("\n", method.Body.Instructions.Select(i => i.OpCode.Name + ":" + Operand(i.Operand, method, maskStrings)).ToArray()) +
            "\nlocals:" + String.Join(",", method.Body.Variables.Select(v => v.VariableType.FullName).ToArray()) +
            "\ninit:" + method.Body.InitLocals + "\neh:" + String.Join("|", method.Body.ExceptionHandlers.Select(e =>
                e.HandlerType + ":" + Operand(e.TryStart, method, false) + ":" + Operand(e.TryEnd, method, false) + ":" +
                Operand(e.HandlerStart, method, false) + ":" + Operand(e.HandlerEnd, method, false) + ":" +
                Operand(e.FilterStart, method, false) + ":" + (e.CatchType == null ? "" : e.CatchType.FullName)).ToArray());
    }
    static object Inspect(string path)
    {
        using (var assembly = AssemblyDefinition.ReadAssembly(path))
            return InspectAssembly(assembly);
    }
    static object InspectAssembly(AssemblyDefinition assembly)
        {
            var plans = Plans(assembly.MainModule);
            return new { schema = 1, assembly = assembly.Name.FullName, runtime = assembly.MainModule.RuntimeVersion,
                public_key = assembly.Name.HasPublicKey, patched = Patched(assembly.MainModule),
                references = assembly.MainModule.AssemblyReferences.Select(r => r.FullName).ToArray(),
                units = plans.SelectMany(p => p.Units).ToArray(),
                method_shapes = plans.ToDictionary(p => p.Method.FullName, p => Hash(Body(p.Method, true))) };
    }
    static MethodReference StringMethod(ModuleDefinition module, string name, TypeReference result, params TypeReference[] args)
    {
        var m = new MethodReference(name, result, module.TypeSystem.String) { HasThis = name != "Format" };
        foreach (var t in args) m.Parameters.Add(new ParameterDefinition(t));
        return m;
    }
    static MethodDefinition Find(TypeDefinition type, string name, int count)
    {
        return type.Methods.Single(m => m.Name == name && m.Parameters.Count == count);
    }
    static MethodDefinition FormatHelper(ModuleDefinition module, TypeDefinition parser)
    {
        var context = module.GetType("Pawley.StarDynasties.Engine.Text.TextContext");
        var lazy = module.GetType("Pawley.StarDynasties.Engine.Text.LazyText");
        var method = new MethodDefinition(Helper, MethodAttributes.Private | MethodAttributes.Static | MethodAttributes.HideBySig, lazy);
        method.Parameters.Add(new ParameterDefinition("text", ParameterAttributes.None, lazy));
        method.Parameters.Add(new ParameterDefinition("context", ParameterAttributes.None, context));
        method.Parameters.Add(new ParameterDefinition("reference", ParameterAttributes.None, module.TypeSystem.Object));
        method.Parameters.Add(new ParameterDefinition("template", ParameterAttributes.None, module.TypeSystem.String));
        parser.Methods.Add(method);
        method.Body.InitLocals = true;
        var index = new VariableDefinition(module.TypeSystem.Int32);
        method.Body.Variables.Add(index);
        var il = method.Body.GetILProcessor();
        il.Emit(OpCodes.Ldarg_3); il.Emit(OpCodes.Ldstr, "{0}");
        il.Emit(OpCodes.Callvirt, StringMethod(module, "IndexOf", module.TypeSystem.Int32, module.TypeSystem.String));
        il.Emit(OpCodes.Stloc, index);
        il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldarg_1);
        il.Emit(OpCodes.Ldarg_3); il.Emit(OpCodes.Ldc_I4_0); il.Emit(OpCodes.Ldloc, index);
        il.Emit(OpCodes.Callvirt, StringMethod(module, "Substring", module.TypeSystem.String, module.TypeSystem.Int32, module.TypeSystem.Int32));
        il.Emit(OpCodes.Ldarg_2);
        il.Emit(OpCodes.Ldarg_3); il.Emit(OpCodes.Ldloc, index); il.Emit(OpCodes.Ldc_I4_3); il.Emit(OpCodes.Add);
        il.Emit(OpCodes.Callvirt, StringMethod(module, "Substring", module.TypeSystem.String, module.TypeSystem.Int32));
        for (int i = 0; i < 6; i++) il.Emit(OpCodes.Ldnull);
        il.Emit(OpCodes.Callvirt, Find(lazy, "Append", 10)); il.Emit(OpCodes.Ret);
        return method;
    }
    static MethodDefinition CharacterVerbHelper(ModuleDefinition module, TypeDefinition parser, MethodDefinition format)
    {
        var parsingContext = module.GetType("Pawley.StarDynasties.Engine.Text.Parsing.ParsingContext");
        var character = module.GetType("Pawley.StarDynasties.Engine.Character");
        var method = new MethodDefinition(CharHelper, MethodAttributes.Private | MethodAttributes.HideBySig, module.TypeSystem.Object);
        method.Parameters.Add(new ParameterDefinition("context", ParameterAttributes.None, parsingContext));
        method.Parameters.Add(new ParameterDefinition("character", ParameterAttributes.None, character));
        foreach (string n in new[] { "player", "visible", "unknown", "substitute" })
            method.Parameters.Add(new ParameterDefinition(n, ParameterAttributes.None, module.TypeSystem.String));
        parser.Methods.Add(method);
        method.Body.InitLocals = true;
        var template = new VariableDefinition(module.TypeSystem.String);
        method.Body.Variables.Add(template);
        var il = method.Body.GetILProcessor();
        var nonNull = Instruction.Create(OpCodes.Nop);
        var notPlayer = Instruction.Create(OpCodes.Nop);
        var invisible = Instruction.Create(OpCodes.Nop);
        var render = Instruction.Create(OpCodes.Nop);
        il.Emit(OpCodes.Ldarg_2); il.Emit(OpCodes.Brtrue, nonNull);
        il.Emit(OpCodes.Ldstr, "[Null parameter]"); il.Emit(OpCodes.Ret); il.Append(nonNull);
        il.Emit(OpCodes.Ldarg_2); il.Emit(OpCodes.Callvirt, Find(character, "IsPlayerCharacter", 0)); il.Emit(OpCodes.Brfalse, notPlayer);
        il.Emit(OpCodes.Ldarg_3); il.Emit(OpCodes.Stloc, template); il.Emit(OpCodes.Br, render); il.Append(notPlayer);
        il.Emit(OpCodes.Ldarg_2); il.Emit(OpCodes.Callvirt, Find(character, "IsVisible", 0)); il.Emit(OpCodes.Brfalse, invisible);
        il.Emit(OpCodes.Ldarg, method.Parameters[3]); il.Emit(OpCodes.Stloc, template); il.Emit(OpCodes.Br, render); il.Append(invisible);
        il.Emit(OpCodes.Ldarg, method.Parameters[4]); il.Emit(OpCodes.Stloc, template); il.Append(render);
        il.Emit(OpCodes.Ldarga, method.Parameters[0]); il.Emit(OpCodes.Call, Find(parsingContext, "GetLazyText", 0));
        il.Emit(OpCodes.Ldarg_1); il.Emit(OpCodes.Ldfld, parsingContext.Fields.Single(f => f.Name == "TextContext"));
        il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldarg_2); il.Emit(OpCodes.Ldarg, method.Parameters[5]);
        il.Emit(OpCodes.Call, Find(parser, "DInternal", 2)); il.Emit(OpCodes.Ldloc, template);
        il.Emit(OpCodes.Call, format); il.Emit(OpCodes.Ret);
        return method;
    }
    static void Rewrite(string source, string payload, string destination)
    {
        EnsureOutput(source, destination);
        var values = Json.Deserialize<Dictionary<string, string>>(File.ReadAllText(payload, Encoding.UTF8));
        File.WriteAllBytes(destination, RewriteBytes(File.ReadAllBytes(source), values));
    }
    static byte[] RewriteBytes(byte[] original, Dictionary<string, string> values)
    {
        byte[] rebuilt;
        using (var assembly = AssemblyDefinition.ReadAssembly(new MemoryStream(original)))
        {
            var module = assembly.MainModule;
            if (assembly.Name.HasPublicKey || (module.Attributes & ModuleAttributes.ILOnly) == 0 || Patched(module))
                throw new InvalidDataException("Only original, unsigned, IL-only assemblies may be built");
            var plans = Plans(module);
            var known = new HashSet<string>(plans.SelectMany(p => p.Units).Select(u => u.key));
            if (values.Keys.Any(k => !known.Contains(k))) throw new InvalidDataException("Unknown grammar key");
            Func<Unit, string> value = u => values.ContainsKey(u.key) ? values[u.key] : u.EN;
            foreach (var u in plans.SelectMany(p => p.Units))
            {
                string v = value(u);
                if (u.argument && (v.Split(new[] { "{0}" }, StringSplitOptions.None).Length != 2 || v.Replace("{0}", "").IndexOfAny(new[] { '{', '}' }) >= 0))
                    throw new InvalidDataException("Reference templates require exactly one {0}");
                if (!u.empty_allowed && String.IsNullOrWhiteSpace(v)) throw new InvalidDataException("Empty required grammar text");
            }
            var parser = module.GetType(Parser);
            var format = FormatHelper(module, parser);
            var charVerb = CharacterVerbHelper(module, parser, format);
            var parsingContext = module.GetType("Pawley.StarDynasties.Engine.Text.Parsing.ParsingContext");
            var lazy = module.GetType("Pawley.StarDynasties.Engine.Text.LazyText");
            foreach (var plan in plans)
            {
                var m = plan.Method;
                if (plan.Kind == "pronoun-phrase")
                {
                    m.Body = new MethodBody(m);
                    var il = m.Body.GetILProcessor();
                    var nonNull = Instruction.Create(OpCodes.Nop);
                    il.Emit(OpCodes.Ldarg_2); il.Emit(OpCodes.Brtrue, nonNull); il.Emit(OpCodes.Ldstr, "[Null parameter]"); il.Emit(OpCodes.Ret); il.Append(nonNull);
                    il.Emit(OpCodes.Ldarga, m.Parameters[0]); il.Emit(OpCodes.Call, Find(parsingContext, "GetLazyText", 0));
                    il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldarg_2);
                    foreach (var u in plan.Units) il.Emit(OpCodes.Ldstr, value(u));
                    il.Emit(OpCodes.Call, Find(parser, "pronoun", 5));
                    il.Emit(OpCodes.Ldarg_1); il.Emit(OpCodes.Ldfld, parsingContext.Fields.Single(f => f.Name == "TextContext"));
                    il.Emit(OpCodes.Callvirt, lazy.Methods.Single(x => x.Name == "Append" && x.Parameters.Count == 2 && x.Parameters[0].ParameterType.FullName == "System.Object"));
                    il.Emit(OpCodes.Ret);
                }
                else if (plan.Kind == "character-verb")
                {
                    m.Body = new MethodBody(m);
                    var il = m.Body.GetILProcessor();
                    if (Char.IsUpper(m.Name[0]))
                    {
                        il.Emit(OpCodes.Ldarga, m.Parameters[0]); il.Emit(OpCodes.Call, Find(parsingContext, "GetLazyText", 0));
                    }
                    il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldarg_1); il.Emit(OpCodes.Ldarg_2);
                    foreach (var u in plan.Units) il.Emit(OpCodes.Ldstr, value(u));
                    il.Emit(OpCodes.Ldarg_3); il.Emit(OpCodes.Call, charVerb);
                    if (Char.IsUpper(m.Name[0]))
                    {
                        il.Emit(OpCodes.Ldarg_1); il.Emit(OpCodes.Ldfld, parsingContext.Fields.Single(f => f.Name == "TextContext"));
                        il.Emit(OpCodes.Callvirt, lazy.Methods.Single(x => x.Name == "Append" && x.Parameters.Count == 2 && x.Parameters[0].ParameterType.FullName == "System.Object"));
                        il.Emit(OpCodes.Callvirt, Find(lazy, "UpperFirst", 0));
                    }
                    il.Emit(OpCodes.Ret);
                }
                else
                {
                    foreach (var u in plan.Units) plan.Strings[u.slot].Operand = value(u);
                    if (plan.Kind == "possessive")
                    {
                        var text = plan.Strings[2];
                        var cursor = text.Next;
                        for (int i = 0; i < 7; i++)
                        {
                            if (cursor == null || cursor.OpCode != OpCodes.Ldnull) throw new InvalidDataException("Possessive stack shape mismatch");
                            cursor.OpCode = OpCodes.Nop; cursor = cursor.Next;
                        }
                        if (cursor == null || cursor.OpCode != OpCodes.Callvirt || ((MethodReference)cursor.Operand).Name != "Append")
                            throw new InvalidDataException("Possessive append call mismatch");
                        cursor.OpCode = OpCodes.Call; cursor.Operand = format;
                    }
                    else if (plan.Kind == "kinship-template")
                    {
                        var calls = m.Body.Instructions.Where(i => i.OpCode == OpCodes.Call && i.Operand is MethodReference &&
                            ((MethodReference)i.Operand).DeclaringType.FullName == "System.String" && ((MethodReference)i.Operand).Name == "Concat").ToArray();
                        if (calls.Length != 5) throw new InvalidDataException("Kinship concat call shape mismatch");
                        foreach (var call in calls) call.Operand = StringMethod(module, "Format", module.TypeSystem.String, module.TypeSystem.String, module.TypeSystem.Object);
                    }
                }
            }
            module.Mvid = assembly.MainModule.Mvid;
            using (var output = new MemoryStream())
            {
                assembly.Write(output, new WriterParameters { Timestamp = 0 });
                rebuilt = output.ToArray();
            }
        }
        using (var a = AssemblyDefinition.ReadAssembly(new MemoryStream(original)))
        using (var b = AssemblyDefinition.ReadAssembly(new MemoryStream(rebuilt))) VerifyAssemblies(a, b, true);
        return rebuilt;
    }
    static string Metadata(AssemblyDefinition assembly)
    {
        var lines = new List<string> { assembly.Name.FullName, assembly.MainModule.RuntimeVersion, assembly.MainModule.Kind.ToString(), assembly.MainModule.Architecture.ToString() };
        lines.AddRange(assembly.MainModule.AssemblyReferences.Select(r => "ref:" + r.FullName));
        foreach (var t in Types(assembly.MainModule))
        {
            lines.Add("type:" + t.FullName + ":" + t.Attributes + ":" + (t.BaseType == null ? "" : t.BaseType.FullName));
            lines.AddRange(t.Interfaces.Select(i => "interface:" + i.InterfaceType.FullName));
            lines.AddRange(t.Fields.Select(f => "field:" + f.FullName + ":" + f.Attributes + ":" + Json.Serialize(f.Constant)));
            lines.AddRange(t.Properties.Select(p => "property:" + p.FullName + ":" + p.Attributes));
            lines.AddRange(t.Events.Select(e => "event:" + e.FullName + ":" + e.Attributes));
            foreach (var m in t.Methods.Where(m => m.Name != Helper && m.Name != CharHelper))
                lines.Add("method:" + m.FullName + ":" + m.Attributes + ":" + m.ImplAttributes + ":" +
                    String.Join("|", m.Parameters.Select(p => p.Name + ":" + p.Attributes + ":" + Json.Serialize(p.Constant)).ToArray()));
        }
        return String.Join("\n", lines.ToArray());
    }
    static void Verify(string original, string rebuilt, bool allowGrammar)
    {
        using (var a = AssemblyDefinition.ReadAssembly(original))
        using (var b = AssemblyDefinition.ReadAssembly(rebuilt))
            VerifyAssemblies(a, b, allowGrammar);
    }
    static void VerifyAssemblies(AssemblyDefinition a, AssemblyDefinition b, bool allowGrammar)
        {
            if (Metadata(a) != Metadata(b)) throw new InvalidDataException("Assembly metadata/reference changes outside approved helpers");
            var allowed = allowGrammar ? new HashSet<string>(Plans(a.MainModule).Select(p => p.Method.FullName)) : new HashSet<string>();
            var methods = Types(b.MainModule).SelectMany(t => t.Methods).ToDictionary(m => m.FullName);
            foreach (var method in Types(a.MainModule).SelectMany(t => t.Methods))
            {
                MethodDefinition other;
                if (!methods.TryGetValue(method.FullName, out other)) throw new InvalidDataException("Method removed");
                if (!allowed.Contains(method.FullName) && Body(method, false) != Body(other, false))
                    throw new InvalidDataException("Unrelated method body changed: " + method.FullName);
            }
            var ra = a.MainModule.Resources.OfType<EmbeddedResource>().ToDictionary(r => r.Name, r => Convert.ToBase64String(r.GetResourceData()));
            var rb = b.MainModule.Resources.OfType<EmbeddedResource>().ToDictionary(r => r.Name, r => Convert.ToBase64String(r.GetResourceData()));
            if (Json.Serialize(ra) != Json.Serialize(rb)) throw new InvalidDataException("Embedded resources changed");
    }
    static void EnsureOutput(string input, string output)
    {
        if (String.Equals(Path.GetFullPath(input), Path.GetFullPath(output), StringComparison.OrdinalIgnoreCase)) throw new InvalidDataException("Original input is read-only");
        var directory = new DirectoryInfo(Path.GetDirectoryName(Path.GetFullPath(output)));
        while (directory != null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "StarDynasties.exe")) && Directory.Exists(Path.Combine(directory.FullName, "StarDynasties_Data")))
                throw new InvalidDataException("Writing to the game installation is forbidden");
            directory = directory.Parent;
        }
    }
    static byte[] DecodeAssembly(string input)
    {
        if (String.IsNullOrWhiteSpace(input))
            throw new InvalidDataException("Assembly input is empty; provide a base64-encoded managed DLL");
        return Convert.FromBase64String(input);
    }
    [System.Runtime.CompilerServices.MethodImpl(System.Runtime.CompilerServices.MethodImplOptions.NoInlining)]
    public static int Main(string[] args)
    {
        Console.OutputEncoding = new UTF8Encoding(false);
        Console.InputEncoding = new UTF8Encoding(false);
        try
        {
            if (args.Length == 1 && args[0] == "inspect-stdin")
            {
                using (var a = AssemblyDefinition.ReadAssembly(new MemoryStream(DecodeAssembly(Console.In.ReadToEnd()))))
                    Console.Write(Json.Serialize(InspectAssembly(a)));
            }
            else if (args.Length == 1 && args[0] == "rewrite-stdin")
            {
                var input = Json.Deserialize<Dictionary<string, object>>(Console.In.ReadToEnd());
                var values = Json.Deserialize<Dictionary<string, string>>(Json.Serialize(input["translations"]));
                var output = RewriteBytes(DecodeAssembly((string)input["assembly"]), values);
                Console.Write(Json.Serialize(new { assembly = Convert.ToBase64String(output) }));
            }
            else if (args.Length == 3 && args[0] == "inspect")
            {
                EnsureOutput(args[1], args[2]);
                File.WriteAllText(args[2], Json.Serialize(Inspect(args[1])), new UTF8Encoding(false));
            }
            else if (args.Length == 4 && args[0] == "rewrite") Rewrite(args[1], args[2], args[3]);
            else if (args.Length == 3 && args[0] == "verify") Verify(args[1], args[2], true);
            else if (args.Length == 3 && args[0] == "roundtrip")
            {
                EnsureOutput(args[1], args[2]);
                using (var a = AssemblyDefinition.ReadAssembly(args[1])) a.Write(args[2], new WriterParameters { Timestamp = 0 });
                Verify(args[1], args[2], false);
            }
            else throw new InvalidDataException("inspect IN OUT.json | rewrite IN payload.json OUT | verify IN OUT | roundtrip IN OUT");
            return 0;
        }
        catch (Exception e) { Console.Error.WriteLine("ERROR: " + e.GetType().Name + ": " + e.Message); return 1; }
    }
}
