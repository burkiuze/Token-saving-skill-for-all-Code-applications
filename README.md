# Token Saver Skills

**Claude Code, Codex, opencode, ZCode, Gemini CLI, Cursor ve GitHub Copilot için ortak skill paketi.** Kaliteden ödün vermeden token tüketimini ciddi ölçüde düşürür ve işi hızlandırır. Ajanın her oturumda kodu baştan sona okumasını engelleyen düzenli bir çalışma akışı kurar. Oturumlar ve araçlar arasında kalıcı, aranabilir bir hafıza tutar.

> English summary at the bottom.

---

## Sorun

Kodlama ajanları tokenlerin ve zamanın çoğunu şu işlerde harcar:

1. **Keşif.** Her yeni oturumda repoyu yeniden tarar (`ls -R`, `cat`, "bir de şu dosyaya bakayım").
2. **Tam dosya okuma.** 1.000 satırlık dosyayı 20 satırlık bir fonksiyon için açar (≈12.000 token).
3. **Log seli.** Filtresiz test veya build çıktısı tek seferde 5.000–50.000 token tutar. Her düzenlemeden sonra tüm test paketini koşturmak dakikalar sürer.
4. **Unutma.** Oturum kapanınca öğrendiklerini (komutlar, tuzaklar, çözülmüş hatalar, kullanıcı tercihleri) kaybeder ve hepsini yeniden keşfeder.
5. **Tekrarlayan iş.** Aynı değişikliği 40 dosyada tek tek okuyup düzenler.
6. **Tahmin.** Kütüphane API'sini tahmin eder, çalışmayınca tekrar dener ya da bağımlılık kaynak kodunu okur.
7. **Gizli vergi.** Şişkin CLAUDE.md/AGENTS.md dosyaları ve açık MCP sunucuları **her mesajda** binlerce token ekler.

## Çözüm: 11 skill ve her zaman açık kısa bir kural bloğu

| Skill | Ne yapar | Hangi israfı keser |
|---|---|---|
| `token-saver` | Ana protokol: boyutla → hafızadan başla → ara → dar oku → minimal düzenle → dar doğrula → kaydet. Kalite korumalarını da içerir. | Hepsi |
| `task-triage` | İşi XS/S/M/L olarak boyutlar. Küçük iş birkaç adımda biter, büyük iş sadece yeterli planla ilerler. | Gereksiz süreç, yeniden yapılan iş |
| `repo-map` | `.codemap/MAP.md`: her dosya, içindeki semboller ve **satır numaraları**. Artımlıdır, yalnızca değişen dosyaları yeniden işler. `find`, `outline`, `show`, `status` komutları var. | Keşif |
| `smart-read` | Önce bul, sonra dosya iskeletine bak, sonra yalnızca gereken satır aralığını oku. Kilit, generated ve minified dosyalar okunmaz. | Tam dosya okuma |
| `quiet-run` | `quiet_run.py -- <komut>`: yalnızca çıkış kodunu, hataları ve özeti basar. Tam log diske yazılır. | Log seli |
| `test-impact` | `affected_tests.py`: değişen dosyalardan etkilenen testleri bulur ve hazır dar komutu verir (pytest, Jest, Vitest, Mocha, Go, Maven, Gradle, .NET, RSpec…). | Yavaş geri bildirim, dev loglar |
| `session-memory` | `.codemap/SESSION.md`: görevin çalışma hafızası. Bağlam sıkıştırmasından ve oturum değişiminden sonra kalınan yerden devam edilir. | Görev içi unutma |
| `persistent-memory` | **Kalıcı hafıza.** `memory.py`: proje (`.codemap/memory.jsonl`) ve global (`~/.agents/memory.jsonl`) hafıza. BM25 aramasıyla yalnızca ilgili kayıtları getirir. Bağlı dosya değişince kaydı "doğrula" diye işaretler. | Oturumlar arası unutma |
| `bulk-edit` | `bulk_replace.py`: repo genelinde önizlemeli bul-değiştir. Sözdizimi farkında araçlar için rehber de içerir (LSP rename, ast-grep, codemod). | Dosya dosya tekrar eden iş |
| `api-lookup` | Kurulu sürümü ve tam imzayı tek komutla öğrenir (`go doc`, `inspect.signature`, `.d.ts` grep…). | Tahmin ve deneme, bağımlılık kodu okuma |
| `context-audit` | `context_audit.py`: her istekte ödenen sabit yükü ölçer (talimat dosyaları, `@import`'lar, skill açıklamaları, MCP sunucuları) ve ne kırpılacağını söyler. | Gizli token vergisi |

Buna ek olarak `AGENTS.md`, `CLAUDE.md` ve `GEMINI.md` dosyalarına yaklaşık 500 tokenlik bir **kural bloğu** eklenir. Toplam sabit maliyet yaklaşık 1.450 tokendir: kural bloğu ve 11 skill açıklaması yaklaşık 950 token. Skill gövdeleri (her biri 600–1.100 token) yalnızca gerektiğinde yüklenir.

## Gerçek ölçümler

**Kod haritası:** `repomap.py build` beş açık kaynak repoda çalıştırıldı (sığ klon; token ≈ bayt / 4).

| Repo | Kaynak dosya | Kaynak boyutu | Harita (MAP.md) | Oran |
|---|---:|---:|---:|---:|
| expressjs/express (JS) | 141 | ~137k token | ~2,6k token | 53x |
| gin-gonic/gin (Go) | 100 | ~175k token | ~3,5k token | 49x |
| BurntSushi/ripgrep (Rust) | 116 | ~484k token | ~10,5k token | 46x |
| psf/requests (Python) | 45 | ~104k token | ~2,8k token | 37x |
| spring-petclinic (Java) | 58 | ~40k token | ~2,7k token | 15x |

İlk build 0,05–0,4 saniye sürdü. Sonraki build'ler yalnızca değişen dosyaları işler.

**Log kırpma:** `quiet_run.py` ile 2.303 satırlık başarısız bir test çıktısı yaklaşık 12 satıra indi. Traceback ve "1 failed" özeti korundu.

**Etkilenen testler:** `affected_tests.py` sonuçları:
- requests'te `auth.py` ve `utils.py` değişince 9 test dosyasından 3'ünü seçti.
- spring-petclinic'te `OwnerController.java` için `mvn -q -Dtest=OwnerControllerTests test` önerdi.
- gin'de değişen paketler için `go test . ./binding` önerdi.

**Toplu değişiklik:** `bulk_replace.py` gin'de 8 dosyadaki 19 `c.JSON(` çağrısını tek bir önizlemede gösterdi. `--apply` ile hepsi tek komutta değişir. Aynı iş normalde 8 okuma ve 19 düzenleme gerektirirdi.

Gerçek tasarruf göreve göre değişir. Ajan normalde ne kadar keşif yapıyor ve ne kadar test koşturuyorsa kazanç o kadar büyük olur.

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

`.agents/skills` açık [Agent Skills](https://agentskills.io) standardının ortak klasörüdür. Claude Code dışındaki tüm araçlar burayı okur, bu yüzden skill'ler tek bir kopyayla hepsinde çalışır. Hafıza dosyaları (`.codemap/*`, `~/.agents/memory.jsonl`) düz metindir ve araçtan bağımsızdır: Claude Code'da öğrenilen bir şeyi Codex veya ZCode da kullanır.

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

### Güncelleme
`git pull` yapın ve `./install.sh` (veya `install.ps1`) komutunu tekrar çalıştırın. Kurulum idempotenttir: kural bloğu işaretçilerin arasında yerinde güncellenir, dosyadaki diğer içeriğe dokunulmaz. `--link` ile kurduysanız `git pull` yeterli.

### Seçenekler
| Amaç | bash | PowerShell |
|---|---|---|
| Tek projeye kur (commit'lenebilir, takımla paylaşılır) | `./install.sh --project ~/kod/app` | `.\install.ps1 -Project C:\kod\app` |
| Yalnızca belirli araçlar | `--tools claude,codex,zcode` | `-Tools claude,codex,zcode` |
| Kurallara dokunmadan sadece skill'leri kur | `--no-rules` | `-NoRules` |
| `git pull` ile otomatik güncelle (symlink) | `--link` | (kopyalar; güncellemek için tekrar çalıştır) |
| Kaldır | `--uninstall` | `-Uninstall` |
| Önce ne yapacağını gör | `--dry-run` | `-DryRun` |

**Gereksinim:** yardımcı scriptler için Python 3.8 veya üzeri yeterli, harici paket gerekmez. Python yoksa skill'ler `rg`/`grep` yedek yollarını kullanır.

## Kullanım

Ekstra bir şey yapmanız gerekmez. Kural bloğu ajanı her görevde şu döngüye sokar:

```
boyutla (XS/S/M/L) → SESSION.md + memory brief/recall → harita → ara (find / rg) → dar oku
   → minimal / toplu düzenle → etkilenen testler (quiet) → tam suite bir kez → SESSION.md + memory add
```

Elle de kullanabilirsiniz (komutları repo içinde çalıştırın; `S` = skill klasörü, ör. `~/.claude/skills`):

```bash
# harita
python3 $S/repo-map/scripts/repomap.py build             # oluştur/güncelle (artımlı)
python3 $S/repo-map/scripts/repomap.py find Router       # sembol nerede? -> path:line
python3 $S/repo-map/scripts/repomap.py status            # son build'den beri değişenler
# kalıcı hafıza
python3 $S/persistent-memory/scripts/memory.py add "Tek test: pnpm vitest run src/x.test.ts -t ad" --kind cmd
python3 $S/persistent-memory/scripts/memory.py add "Kullanıcı Türkçe açıklama istiyor" --kind pref --global
python3 $S/persistent-memory/scripts/memory.py recall "vitest tek test"
python3 $S/persistent-memory/scripts/memory.py brief     # oturum başı özeti (~300 token)
# testler ve loglar
python3 $S/test-impact/scripts/affected_tests.py         # sadece etkilenen testler + komut
python3 $S/quiet-run/scripts/quiet_run.py -- npm test    # yalnızca hatalar ve özet
# toplu değişiklik (önce önizleme, sonra --apply)
python3 $S/bulk-edit/scripts/bulk_replace.py "oldApi\(" "newApi(" --glob "*.ts"
# gizli token vergisi
python3 $S/context-audit/scripts/context_audit.py
```

Ajana doğrudan şöyle de söyleyebilirsiniz: "bunu hafızaya kaydet", "etkilenen testleri çalıştır", "context audit yap", "bunu bulk-edit ile değiştir".

`.codemap/` klasörü kendi `.gitignore` dosyasını otomatik oluşturur. Yalnızca `NOTES.md` ve `memory.jsonl` commit'lenir, böylece takım arkadaşlarınızın ajanları da aynı bilgilerden başlar. Hafızayı gizli tutmak isterseniz `.codemap/.gitignore` içinden `!memory.jsonl` satırını silin.

## Performans güvencesi

Tasarruf **alakasız okumayı, tekrarı ve gereksiz süreci keserek** yapılır, gerekli işten kısılarak değil. Skill'lerde şu kurallar yazılıdır:

- Görülmemiş kod hakkında asla tahmin yürütülmez. Değiştirilecek fonksiyonun tamamı okunur, imza değişiyorsa çağrı yerleri bulunur.
- Önce etkilenen testler koşulur, iş "bitti" denmeden önce **tam test paketi bir kez** çalıştırılır.
- Hafıza kayıtları dosya hash'iyle bağlanır. Dosya değişince kayıt `!! verify` olarak işaretlenir, eski bilgi sessizce yanıltmaz.
- Toplu değişiklik önce önizlenir. Sonrasında `git diff --stat`, artık eşleşme araması ve testlerle doğrulanır.
- Görev boyutu belirsizse küçük işin sadeliği, büyük işin doğrulaması seçilir. Sürprizde boyut büyütülür, kalite asla azaltılmaz.

## Opsiyonel: Claude Code'da otomatik başlangıç (SessionStart hook)

`~/.claude/settings.json` dosyasına eklenirse her oturum başında ve sıkıştırmadan sonra harita güncellenir ve hafıza özeti ajana verilir:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup|resume|compact",
        "hooks": [
          {
            "type": "command",
            "command": "cd \"${CLAUDE_PROJECT_DIR:-.}\" && git rev-parse --is-inside-work-tree >/dev/null 2>&1 && python3 ~/.claude/skills/repo-map/scripts/repomap.py build && python3 ~/.claude/skills/persistent-memory/scripts/memory.py brief && { [ -f .codemap/SESSION.md ] && echo 'Unfinished task: read .codemap/SESSION.md first.'; true; } || true"
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
  token-saver/            ana protokol
  task-triage/            XS/S/M/L iş boyutlandırma ve hız kuralları
  repo-map/               kod haritası (scripts/repomap.py, 30+ dil) + templates/NOTES.md
  smart-read/             bul → iskelet → satır aralığı
  quiet-run/              scripts/quiet_run.py
  test-impact/            scripts/affected_tests.py
  session-memory/         SESSION.md görev hafızası
  persistent-memory/      scripts/memory.py (kalıcı, aranabilir hafıza)
  bulk-edit/              scripts/bulk_replace.py
  api-lookup/             sürüm ve imza sorgulama rehberi
  context-audit/          scripts/context_audit.py
rules/token-saver-block.md   AGENTS.md / CLAUDE.md için her zaman açık blok
install.sh  install.ps1      kurulum / güncelleme / kaldırma
tests/test_scripts.py        python3 -m unittest discover tests
```

Harita şu dilleri tanır: JS/TS (Vue, Svelte, Astro dahil), Python, Go, Rust, Java, Kotlin, C#, Swift, Dart, C/C++, PHP, Ruby, Scala, Elixir, Lua, Shell, PowerShell, Perl, R, Julia, Zig, Haskell, OCaml, Clojure, SQL, Protobuf, GraphQL, Terraform, Markdown, Makefile ve Dockerfile.

---

## English summary

**Token Saver Skills** is one pack of 11 skills for Claude Code, Codex, opencode, ZCode, Gemini CLI, Cursor and GitHub Copilot. It cuts token use a lot and speeds up work without lowering output quality.

- **token-saver**, **task-triage**: the core loop, plus task sizing so small jobs stay small and big jobs get just enough planning.
- **repo-map**, **smart-read**: an incremental code map with symbols and line numbers (15–53x smaller than the source it indexes), then search → outline → line-range reads.
- **quiet-run**, **test-impact**: capped, failure-focused command output, and running only the tests affected by your change first.
- **session-memory**, **persistent-memory**: task scratchpad plus long-term, searchable memory (BM25). It works across sessions and tools, and memories are flagged when their linked files change.
- **bulk-edit**, **api-lookup**, **context-audit**: previewed repo-wide replacements; exact API facts from the installed version; and a report of the per-request token tax from instruction files, skills and MCP servers.

Install with `./install.sh` or `install.ps1` (`--project DIR`, `--tools`, `--link`, `--uninstall`, `--dry-run`). The scripts need Python 3.8+ and no other dependencies. Always-on cost is about 1.45k tokens (rules block plus skill descriptions).

## Lisans
Apache-2.0
