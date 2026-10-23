// Isolated real-engine grammar tests. These fixture substitutions NEVER ship.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Runtime.Serialization;
using System.Web.Script.Serialization;
using Mono.Cecil;
using Mono.Cecil.Cil;
using FieldAttributes = Mono.Cecil.FieldAttributes;
using MethodBody = Mono.Cecil.Cil.MethodBody;

public static class GrammarRuntimeTests
{
    static readonly BindingFlags Flags = BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance | BindingFlags.Static;
    static int Checks;
    static void Equal(object actual, string expected, string label)
    {
        string value = actual == null ? "<null>" : actual.ToString();
        if (value != expected) throw new Exception(label + ": expected " + expected + ", got " + value);
        Checks++;
    }
    static object Field(object target, string name)
    {
        return target.GetType().GetField(name, Flags).GetValue(target);
    }
    static void Set(object target, string name, object value)
    {
        target.GetType().GetField(name, Flags).SetValue(target, value);
    }
    static MethodInfo Method(Type type, string name, int args)
    {
        return type.GetMethods(Flags).Single(m => m.Name == name && m.GetParameters().Length == args);
    }
    static void EnsureFixtureOutput(string input, string output)
    {
        if (Path.GetFullPath(input) == Path.GetFullPath(output)) throw new Exception("Original input is read-only");
        var directory = new DirectoryInfo(Path.GetDirectoryName(Path.GetFullPath(output)));
        while (directory != null)
        {
            if (File.Exists(Path.Combine(directory.FullName, "StarDynasties.exe")) && Directory.Exists(Path.Combine(directory.FullName, "StarDynasties_Data")))
                throw new Exception("Fixture must not be written into the game installation");
            directory = directory.Parent;
        }
    }
    static void CopyFixture(string input, string output)
    {
        EnsureFixtureOutput(input, output);
        using (var assembly = AssemblyDefinition.ReadAssembly(input))
        {
            var module = assembly.MainModule;
            var character = module.GetType("Pawley.StarDynasties.Engine.Character");
            foreach (string name in new[] { "IsPlayerCharacter", "IsVisible" })
            {
                var field = new FieldDefinition("__Test" + name, FieldAttributes.Public, module.TypeSystem.Boolean);
                character.Fields.Add(field);
                var method = character.Methods.Single(m => m.Name == name && m.Parameters.Count == 0);
                method.Body = new MethodBody(method);
                var il = method.Body.GetILProcessor();
                il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldfld, field); il.Emit(OpCodes.Ret);
            }
            var lazy = module.GetType("Pawley.StarDynasties.Engine.Text.LazyText");
            var element = module.GetType("Pawley.StarDynasties.Engine.Text.PooledTextElement");
            var append = character.Methods.Single(m => m.Name == "AppendTo");
            append.Body = new MethodBody(append);
            var appendIL = append.Body.GetILProcessor();
            appendIL.Emit(OpCodes.Ldarg_1); appendIL.Emit(OpCodes.Ldstr, "REFERENCE_Ç"); appendIL.Emit(OpCodes.Ldarg_0);
            appendIL.Emit(OpCodes.Call, element.Methods.Single(m => m.Name == "Get" && m.Parameters.Count == 2 && m.Parameters[0].ParameterType.FullName == "System.String" && m.Parameters[1].ParameterType.FullName == "System.Object"));
            appendIL.Emit(OpCodes.Callvirt, lazy.Methods.Single(m => m.Name == "Append" && m.Parameters.Count == 1 && m.Parameters[0].ParameterType.Name == "ITextElement"));
            appendIL.Emit(OpCodes.Pop); appendIL.Emit(OpCodes.Ret);
            var game = module.GetType("Pawley.StarDynasties.Engine.Game");
            foreach (string name in new[] { "PlayerCharacter", "ViewManager" })
            {
                var getter = game.Methods.Single(m => m.Name == "get_" + name);
                var field = new FieldDefinition("__Test" + name, FieldAttributes.Public, getter.ReturnType);
                game.Fields.Add(field);
                getter.Body = new MethodBody(getter);
                var il = getter.Body.GetILProcessor();
                il.Emit(OpCodes.Ldarg_0); il.Emit(OpCodes.Ldfld, field); il.Emit(OpCodes.Ret);
            }
            var view = module.GetType("Pawley.StarDynasties.Engine.Views.ViewManager");
            foreach (var getter in view.Methods.Where(m => m.Name == "GetView" && m.HasGenericParameters))
            {
                getter.Body = new MethodBody(getter) { InitLocals = true };
                var local = new VariableDefinition(getter.ReturnType);
                getter.Body.Variables.Add(local);
                var il = getter.Body.GetILProcessor();
                il.Emit(OpCodes.Ldloca, local); il.Emit(OpCodes.Initobj, getter.ReturnType); il.Emit(OpCodes.Ldloc, local); il.Emit(OpCodes.Ret);
            }
            // Real kinship MapTerm is exercised with controlled source tables, not a campaign/config database.
            var kin = module.GetType("Pawley.StarDynasties.Engine.Simulation.Kinship.KinRelationshipVerbalizer_eng");
            var init = kin.Methods.Single(m => m.Name == ".cctor");
            init.Body = new MethodBody(init); init.Body.GetILProcessor().Emit(OpCodes.Ret);
            var language = module.GetType("Pawley.StarDynasties.Engine.Main").Methods.Single(m => m.Name == "get_Language");
            language.Body = new MethodBody(language);
            language.Body.GetILProcessor().Emit(OpCodes.Ldc_I4_0); language.Body.GetILProcessor().Emit(OpCodes.Ret);
            assembly.Write(output, new WriterParameters { Timestamp = 0 });
        }
    }
    static object NewContext(Assembly assembly)
    {
        var contextType = assembly.GetType("Pawley.StarDynasties.Engine.Text.Parsing.ParsingContext");
        object context = Activator.CreateInstance(contextType);
        var compiledType = assembly.GetType("Pawley.StarDynasties.Engine.Text.Parsing.CompiledScript");
        object compiled = FormatterServices.GetUninitializedObject(compiledType);
        var listField = compiledType.GetField("IntermediateLazyTexts", Flags);
        listField.SetValue(compiled, Activator.CreateInstance(listField.FieldType));
        Set(context, "CompiledScript", compiled);
        var textContext = assembly.GetType("Pawley.StarDynasties.Engine.Text.TextContext");
        Set(context, "TextContext", textContext.GetField("Default", Flags).GetValue(null));
        return context;
    }
    public static int Main(string[] args)
    {
        Console.OutputEncoding = new System.Text.UTF8Encoding(false);
        try
        {
            if (args.Length == 3 && args[0] == "source-change")
            {
                EnsureFixtureOutput(args[1], args[2]);
                using (var assembly = AssemblyDefinition.ReadAssembly(args[1]))
                {
                    var parserDefinition = assembly.MainModule.GetType("Pawley.StarDynasties.Engine.Text.Parsing.ParsingHelper");
                    var method = parserDefinition.Methods.Single(m => m.Name == "he");
                    method.Body.Instructions.Where(i => i.OpCode == OpCodes.Ldstr).ElementAt(2).Operand = "changed-source-female";
                    assembly.Write(args[2], new WriterParameters { Timestamp = 0 });
                }
                return 0;
            }
            if (args.Length != 4) throw new Exception("PATCHED_DLL FIXTURE_DLL ORIGINAL_MANAGED_DIR EXPECTED_JSON");
            CopyFixture(args[0], args[1]);
            AppDomain.CurrentDomain.AssemblyResolve += delegate(object sender, ResolveEventArgs e)
            {
                string file = Path.Combine(args[2], new AssemblyName(e.Name).Name + ".dll");
                return File.Exists(file) ? Assembly.LoadFrom(file) : null;
            };
            var expected = new JavaScriptSerializer().Deserialize<Dictionary<string, string>>(File.ReadAllText(args[3], System.Text.Encoding.UTF8));
            Func<string, string, string> wanted = (method, role) => expected.Single(kv => kv.Key.Contains("::" + method + "(") && kv.Key.EndsWith("#" + role, StringComparison.Ordinal)).Value;
            var a = Assembly.LoadFile(Path.GetFullPath(args[1]));
            Type parserType = a.GetType("Pawley.StarDynasties.Engine.Text.Parsing.ParsingHelper");
            Type characterType = a.GetType("Pawley.StarDynasties.Engine.Character");
            object parser = FormatterServices.GetUninitializedObject(parserType);
            object game = FormatterServices.GetUninitializedObject(a.GetType("Pawley.StarDynasties.Engine.Game"));
            object view = FormatterServices.GetUninitializedObject(a.GetType("Pawley.StarDynasties.Engine.Views.ViewManager"));
            Set(game, "__TestViewManager", view); Set(parser, "Game", game);
            string[] roles = { "player", "male", "female", "unknown" };
            var chars = new object[4];
            for (int i = 0; i < 4; i++)
            {
                chars[i] = FormatterServices.GetUninitializedObject(characterType);
                Set(chars[i], "__TestIsPlayerCharacter", i == 0);
                Set(chars[i], "__TestIsVisible", i != 3);
                var sex = characterType.GetField("<Sex>k__BackingField", Flags);
                sex.SetValue(chars[i], Enum.ToObject(sex.FieldType, i == 2 ? 1 : 0));
                foreach (string name in new[] { "he", "He", "him", "Him", "his", "His" })
                    Equal(Method(parserType, name, 1).Invoke(parser, new[] { chars[i] }), wanted(name, roles[i]), name + ":" + roles[i]);
                Equal(Method(parserType, "himself", 2).Invoke(parser, new[] { chars[i], chars[i] }), wanted("himself", roles[i]), "reflexive:" + roles[i]);
                foreach (string name in new[] { "hehas", "Hehas", "heis", "Heis", "hewas", "Hewas" })
                    Equal(Method(parserType, name, 2).Invoke(parser, new[] { NewContext(a), chars[i] }), wanted(name, roles[i]), name + ":" + roles[i]);
                foreach (string name in new[] { "s", "es" })
                    Equal(Method(parserType, name, 1).Invoke(parser, new[] { chars[i] }), wanted(name, i == 0 ? "player-suffix" : "other-suffix"), name + ":suffix:" + roles[i]);
                Set(game, "__TestPlayerCharacter", i == 0 ? chars[0] : null);
                foreach (string name in new[] { "dhas", "Dhas", "dis", "Dis", "dwas", "Dwas" })
                {
                    string role = i == 0 ? "player-template" : i == 3 ? "unknown-template" : "visible-template";
                    string reference = i == 0 ? wanted("DInternal", "player") : i == 3 ? "FALLBACK_REF" : "REFERENCE_Ç";
                    string answer = wanted(name, role).Replace("{0}", reference);
                    if (Char.IsUpper(name[0])) answer = Char.ToUpperInvariant(answer[0]) + answer.Substring(1);
                    Equal(Method(parserType, name, 3).Invoke(parser, new object[] { NewContext(a), chars[i], "FALLBACK_REF" }), answer, name + ":" + roles[i]);
                }
                foreach (string name in new[] { "d_s", "dp_s", "D_s", "Dp_s" })
                {
                    string key = Char.ToLowerInvariant(name[0]) + name.Substring(1);
                    string answer = i == 0 ? wanted(key, "player") : wanted(key, "reference-template").Replace("{0}", i == 3 ? "FALLBACK_REF" : "REFERENCE_Ç");
                    if (Char.IsUpper(name[0])) answer = Char.ToUpperInvariant(answer[0]) + answer.Substring(1);
                    object[] parameters = key == "d_s" ? new object[] { NewContext(a), chars[i], "FALLBACK_REF" } : new object[] { NewContext(a), chars[i], null, "FALLBACK_REF" };
                    Equal(Method(parserType, name, parameters.Length).Invoke(parser, parameters), answer, name + ":" + roles[i]);
                }
            }
            Equal(Method(parserType, "he", 1).Invoke(parser, new object[] { null }), "[Null parameter]", "null pronoun");
            Equal(Method(parserType, "hehas", 2).Invoke(parser, new object[] { NewContext(a), null }), "[Null parameter]", "null compound");
            var list = Method(parserType, "listAsSentence", 3).Invoke(parser, new object[] { NewContext(a), new object[] { "A", "B", "C" }, null });
            Equal(list, "A, B, " + wanted("listAsSentence", "english-conjunction") + " C", "default conjunction");
            var lazyType = a.GetType("Pawley.StarDynasties.Engine.Text.LazyText");
            var lazy = Method(lazyType, "Get", 9).Invoke(null, new object[9]);
            var marker = new object();
            var elementType = a.GetType("Pawley.StarDynasties.Engine.Text.PooledTextElement");
            var element = elementType.GetMethods(Flags).Single(m => m.Name == "Get" && m.GetParameters().Length == 2 && m.GetParameters()[0].ParameterType == typeof(string) && m.GetParameters()[1].ParameterType == typeof(object)).Invoke(null, new object[] { "LINK_REF", marker });
            var contextObj = Field(NewContext(a), "TextContext");
            var formatted = Method(parserType, "__PtBrFormatReference", 4).Invoke(null, new object[] { lazy, contextObj, element, "prefix_ç {0} suffix_ã" });
            Equal(formatted, "prefix_ç LINK_REF suffix_ã", "reference template prefix/suffix");
            var elements = (IEnumerable)lazyType.GetProperty("ElementList", Flags).GetValue(formatted, null);
            if (!elements.Cast<object>().Any(x => Object.ReferenceEquals(x.GetType().GetProperty("ContextObject", Flags).GetValue(x, null), marker)))
                throw new Exception("Clickable reference context was lost");
            Checks++;
            var kinType = a.GetType("Pawley.StarDynasties.Engine.Simulation.Kinship.KinRelationshipVerbalizer_eng");
            var kin = FormatterServices.GetUninitializedObject(kinType);
            var mapField = kinType.GetField("KinTypeMaps", Flags);
            var maps = (IDictionary)Activator.CreateInstance(mapField.FieldType);
            var determinerType = mapField.FieldType.GetGenericArguments()[0];
            foreach (var number in Enum.GetValues(determinerType)) maps.Add(number, new Dictionary<string, string>());
            mapField.SetValue(kin, maps);
            var mapping = kinType.GetField("KinTypeTermMapping", Flags);
            mapping.SetValue(null, Activator.CreateInstance(mapping.FieldType));
            string[] kinRoles = { "self", "player", "male", "female", "unknown" };
            for (int i = 0; i < kinRoles.Length; i++)
                Equal(Method(kinType, "MapTerm", 2).Invoke(kin, new object[] { "ref", Enum.ToObject(determinerType, i) }),
                    wanted("MapTerm", kinRoles[i]).Replace("{0}", "ref"), "kinship:" + kinRoles[i]);
            var managerType = a.GetType("Pawley.StarDynasties.Engine.Text.Parsing.ParsingManager");
            var manager = FormatterServices.GetUninitializedObject(managerType);
            foreach (var field in managerType.GetFields(Flags).Where(f => !f.IsStatic && f.FieldType.IsGenericType && f.FieldType.GetGenericTypeDefinition() == typeof(Dictionary<,>)))
                field.SetValue(manager, Activator.CreateInstance(field.FieldType));
            Method(parserType, "AddDelegates", 1).Invoke(parser, new[] { manager });
            var compiledType = a.GetType("Pawley.StarDynasties.Engine.Text.Parsing.CompiledScript");
            var compiled = Activator.CreateInstance(compiledType, Flags, null, new object[] { manager,
                "{He(Actor)} / {fb(Missing,\"fallback_çã\")} / {if(isNull(Missing),\"branch_ã\",Actor)}" }, null);
            var text = Method(lazyType, "Get", 9).Invoke(null, new object[9]);
            Method(compiledType, "AppendParsed", 3).Invoke(compiled, new object[] { text,
                new Dictionary<string, object> { { "Actor", chars[0] }, { "Missing", null } }, contextObj });
            Equal(text, wanted("He", "player") + " / fallback_çã / branch_ã", "native parser quoted display arguments");
            Console.WriteLine("{\"runtime_checks\":" + Checks + ",\"clickable_context_preserved\":true,\"actual_engine_grammar_executed\":true,\"native_quoted_arguments_tested\":true,\"fixture_only_substitutions\":[\"character player/visibility\",\"character display\",\"game player/view access and language\",\"kinship source tables\"]}");
            return 0;
        }
        catch (Exception e)
        {
            while (e.InnerException != null) e = e.InnerException;
            Console.Error.WriteLine(e.GetType().Name + ": " + e.Message + "\n" + e.StackTrace);
            return 1;
        }
    }
}
