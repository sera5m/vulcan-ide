# Same idea as Java / C#

| Java / C# | Vulcan |
|-----------|--------|
| Spec + stdlib (`java.lang`, BCL) | **vulcan-lang** BASE — parse, bytecode, opcodes. On every device. |
| javac + JVM / CLR built per OS | **Interpreter** built per device: PC = `rsvm`; watch = same core in the firmware |
| IntelliJ / Visual Studio | **this repo** — editor. Pulls BASE, builds PC VM, runs code. Not a second language. |
| ART / mobile CLR | Watch VM — same BASE, ESP host |

`bootstrap.py` clones https://github.com/sera5m/vulcan-lang if it is not next to the IDE.
