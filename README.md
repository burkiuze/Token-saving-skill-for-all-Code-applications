# Token Saver Skills

**Claude Code, Codex, opencode, ZCode, Gemini CLI, Cursor ve GitHub Copilot için ortak skill paketi.** Kaliteden ödün vermeden token tüketimini ciddi ölçüde düşürür. Ajanın her oturumda kodu baştan sona okumasını engelleyen düzenli bir çalışma akışı kurar.

> English summary at the bottom.

---

## Sorun

Kodlama ajanları tokenlerin çoğunu şu dört işte harcar:

1. **Keşif.** Her yeni oturumda `ls -R`, `cat`, "bir de şu dosyaya bakayım" döngüsüyle repoyu yeniden tarar.
2. **Tam dosya okuma.** 1.000 satırlık dosyayı 20 satırlık bir fonksiyon için açar (≈12.000 token).
3. **Log seli.** Filtresiz test veya build çıktısı tek seferde 5.000–50.000 token tutar.
4. **Unutma.** Bağlam sıkıştırıldığında ya da oturum kapandığında öğrendiklerini kaybeder ve her şeyi yeniden keşfeder.

## Çözüm: 5 skill ve her zaman açık kısa bir kural bloğu

| Skill | Ne yapar | Hangi israfı keser |
|---|---|---|
| `token-saver` | Ana protokol: devam et → yön bul → ara → dar oku → minimal düzenle → sessiz doğrula → kaydet. Kalite korumalarını da içerir. | Hepsi |
| `repo-map` | `.codemap/MAP.md`: her dosya, içindeki sınıf ve fonksiyonlar ve **satır numaraları**. Artımlıdır, yalnızca değişen dosyaları yeniden işler. `find`, `outline`, `show` ve `status` komutları da var. | Keşif |
| `smart-read` | Önce bul, sonra dosya iskeletine bak, sonra yalnızca gereken satır aralığını oku. Kilit, generated ve minified dosyalar asla okunmaz. | Tam dosya okuma |
| `quiet-run` | `quiet_run.py -- <komut>`: yalnızca çıkış kodunu, hata satırlarını ve özeti basar. Tam log dosyaya yazılır. | Log seli |
| `session-memory` | `.codemap/SESSION.md` (görev hafızası) ve `.codemap/NOTES.md` (proje hafızası). Sıkıştırmadan ya da araç değişiminden sonra ajan kaldığı yerden devam eder. | Unutma ve yeniden keşif |

Buna ek olarak `AGENTS.md`, `CLAUDE.md` ve `GEMINI.md` dosyalarına yaklaşık 400 tokenlik bir **kural bloğu** eklenir. Skill'ler yalnızca gerektiğinde yüklenir, kurallar ise her zaman aktiftir.

## Gerçek ölçümler

`repomap.py build` beş açık kaynak repoda çalıştırıldı (sığ klon; token ≈ bayt / 4):

| Repo | Kaynak dosya | Kaynak boyutu | Harita (MAP.md) | Oran |
|---|---:|---:|---:|---:|
| expressjs/express (JS) | 141 | ~137k token | ~2,6k token | 53x |
| gin-gonic/gin (Go) | 100 | ~175k token | ~3,5k token | 49x |
| BurntSushi/ripgrep (Rust) | 116 | ~484k token | ~10,5k token | 46x |
| psf/requests (Python) | 45 | ~104k token | ~2,8k token | 37x |
| spring-petclinic (Java) | 58 | ~40k token | ~2,7k token | 15x |

- İlk build 0,05–0,4 saniye sürdü. Sonraki build'ler yalnızca değişen dosyaları işler.
- `quiet_run.py`: 2.303 satırlık başarısız bir test çıktısı yaklaşık 12 satıra indi. Traceback ve "1 failed" özeti korundu (bkz. `tests/`).

Gerçek tasarruf göreve göre değişir. Ajan normalde ne kadar keşif yapıyorsa kazanç o kadar büyüktür.

## Desteklenen araçlar

| Araç | Skill klasörü (global / proje) | Her zaman açık kurallar (global / proje) |
|---|---|---|
| Claude Code | `~/.claude/skills` / `.claude/skills` | `~/.claude/CLAUDE.md` / `CLAUDE.md` |
| OpenAI Codex | `~/.agents/skills` / `.agents/skills` | `~/.codex/AGENTS.md` / `AGENTS.md` |
| opencode | `~/.agents/skills` / `.agents/skills` | `~/.config/opencode/AGENTS.md` / `AGENTS.md` |
| ZCode (Z.ai) | `~/.agents/skills` / `.agents/skills` | `~/.zcode/AGENTS.md` / `AGENTS.md` |
| Gemini CLI | `~/.agents/skills` / `.agents/skills` | `~/.gemini/GEMINI.md` / `GEMINI.md` |
| Cursor | `~/.agents/skills` / `.agents/skills` | Settings → Rules / `AGENTS.md` |
| GitHub Copilot | `~/.agents/skills` / `.agents/skills` | `~/.copilot/copilot-instructions.md` / `AGENTS.md` |

`.agents/skills` açık [Agent Skills](https://agentskills.io) standardının ortak klasörüdür. Claude Code dışındaki tüm araçlar burayı okur, bu yüzden skill'ler tek bir kopyayla hepsinde çalışır.

## Kurulum

### macOS / Linux / WSL / Git Bash
```bash
git clone https://github.com/burkiuze/Token-saving-skill-for-all-Code-applications.git
cd Token-saving-skill-for-all-Code-applications
./install.sh              # makinede bulunan tüm araçlara global kurulum
```

### Windows (PowerShell)
```powershell
git clone https://github.com/burkiuze/Token-saving-skill-for-all-Code-applications.git
cd Token-saving-skill-for-all-Code-applications
powershell -ExecutionPolicy Bypass -File .\install.ps1
```

### Seçenekler
| Amaç | bash | PowerShell |
|---|---|---|
| Tek projeye kur (takımla paylaşmak için commit'lenebilir) | `./install.sh --project ~/kod/app` | `.\install.ps1 -Project C:\kod\app` |
| Yalnızca belirli araçlar | `--tools claude,codex,zcode` | `-Tools claude,codex,zcode` |
| Kurallara dokunmadan sadece skill'leri kur | `--no-rules` | `-NoRules` |
| `git pull` ile otomatik güncelle (symlink) | `--link` | (kopyalar; güncellemek için tekrar çalıştır) |
| Kaldır | `--uninstall` | `-Uninstall` |
| Önce ne yapacağını gör | `--dry-run` | `-DryRun` |

Kurulum idempotenttir: tekrar çalıştırıldığında kural bloğu işaretçilerin arasında yerinde güncellenir, dosyadaki diğer içeriğe dokunulmaz. Kurulumdan sonra aracı yeniden başlatın.

**Gereksinim:** yardımcı scriptler (`repomap.py`, `quiet_run.py`) için Python 3.8 veya üzeri yeterli, harici paket gerekmez. Python yoksa skill'ler `rg`/`grep` yedek yollarını kullanır.

## Kullanım

Ekstra bir şey yapmanız gerekmez. Kural bloğu ajanı her görevde şu döngüye sokar:

```
SESSION.md / NOTES.md oku → harita (build) → ara (find / rg) → dar oku (satır aralığı)
   → minimal düzenle → dar test (quiet_run) → SESSION.md güncelle
```

Elle de kullanabilirsiniz (komutları repo içinde çalıştırın; `S` = skill klasörü, ör. `~/.claude/skills`):

```bash
python3 $S/repo-map/scripts/repomap.py build          # haritayı oluştur/güncelle (artımlı)
python3 $S/repo-map/scripts/repomap.py status         # son build'den beri değişen dosyalar
python3 $S/repo-map/scripts/repomap.py find Router    # sembol nerede? -> path:line
python3 $S/repo-map/scripts/repomap.py outline src/app.ts
python3 $S/repo-map/scripts/repomap.py show src/api/
python3 $S/quiet-run/scripts/quiet_run.py -- npm test # yalnızca hatalar ve özet
```

Örnek harita satırı:
```
### lib/
response.js 1049L: res.{status:65 links:98 send:126 json:236 jsonp:264 sendStatus:325 ...}
```

Ajana doğrudan şu komutları da verebilirsiniz: "repo-map ile haritayı çıkar", "quiet-run ile testleri çalıştır", "session-memory'ye kaydet".

`.codemap/` klasörü kendi `.gitignore` dosyasını otomatik oluşturur. Yalnızca `NOTES.md` commit'lenir, böylece takım arkadaşlarınızın ajanları da aynı proje notlarından başlar.

## Performans güvencesi

Tasarruf **alakasız okumayı ve tekrarı keserek** yapılır, gerekli okumadan kısılarak değil. Skill'lerde şu kurallar yazılıdır:

- Görülmemiş kod hakkında asla tahmin yürütülmez. Değişiklik ona bağlıysa kod okunur.
- Değiştirilecek fonksiyonun **tamamı** okunur, imza değişiyorsa çağrı yerleri `rg` ile bulunur.
- Küçük dosyalar (<150 satır) parça parça değil, tek seferde okunur.
- İş "bitti" denmeden önce ilgili test, typecheck veya build **her zaman** çalıştırılır.
- Dar yaklaşım iki kez başarısız olursa ajan bilerek genişler, körü körüne denemeye devam etmez.

## Opsiyonel: Claude Code'da otomatik harita (SessionStart hook)

`~/.claude/settings.json` dosyasına eklenirse her oturum başında ve sıkıştırmadan sonra harita güncellenir, ajana tek satırlık bir özet verilir:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|compact",
        "hooks": [
          {
            "type": "command",
            "command": "cd \"${CLAUDE_PROJECT_DIR:-.}\" && git rev-parse --is-inside-work-tree >/dev/null 2>&1 && python3 ~/.claude/skills/repo-map/scripts/repomap.py build && { [ -f .codemap/SESSION.md ] && echo 'Unfinished task: read .codemap/SESSION.md first.'; true; } || true"
          }
        ]
      }
    ]
  }
}
```

## Dosya yapısı

```
skills/
  token-saver/SKILL.md          ana protokol
  repo-map/SKILL.md             kod haritası ve NOTES.md
  repo-map/scripts/repomap.py   harita üreticisi (Python stdlib, 30+ dil)
  repo-map/templates/NOTES.md
  smart-read/SKILL.md           bul → iskelet → satır aralığı
  quiet-run/SKILL.md
  quiet-run/scripts/quiet_run.py
  session-memory/SKILL.md
rules/token-saver-block.md      AGENTS.md / CLAUDE.md için her zaman açık blok
install.sh  install.ps1         kurulum / kaldırma
tests/test_scripts.py           python3 -m unittest discover tests
```

Harita şu dilleri tanır: JS/TS (Vue, Svelte, Astro dahil), Python, Go, Rust, Java, Kotlin, C#, Swift, Dart, C/C++, PHP, Ruby, Scala, Elixir, Lua, Shell, PowerShell, Perl, R, Julia, Zig, Haskell, OCaml, Clojure, SQL, Protobuf, GraphQL, Terraform, Markdown, Makefile ve Dockerfile.

---

## English summary

**Token Saver Skills** is one skill pack for Claude Code, Codex, opencode, ZCode, Gemini CLI, Cursor and GitHub Copilot. It cuts token use a lot without lowering output quality.

- **token-saver** is the core loop: resume → orient → locate → read narrowly → edit minimally → verify quietly → checkpoint. It also carries the quality guardrails.
- **repo-map** keeps an incremental code map (`.codemap/MAP.md`) listing every file with its symbols and line numbers. It has `find`, `outline`, `show` and `status` commands. On real repos the map was 15–53x smaller than the source it indexes.
- **smart-read** means search, then outline, then a line-range read. Lockfiles, vendored, generated and minified files are never opened.
- **quiet-run** runs a command and prints only failures and the summary. The full log is saved to disk. A 2,303-line test log came out as ~12 lines.
- **session-memory** keeps `.codemap/SESSION.md` (task memory) and `NOTES.md` (project memory), so the agent survives context compaction and tool switches without re-reading the codebase.

Install with `./install.sh` (macOS, Linux, WSL, Git Bash) or `install.ps1` (Windows). Add `--project DIR` for a single repo and `--uninstall` to remove everything. The scripts need Python 3.8+ and no other dependencies.

## Lisans
Apache-2.0
