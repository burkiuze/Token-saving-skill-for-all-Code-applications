# Token Saver Skills 2.0

Kodlama ajanlarının gereksiz dosya okumalarını, tekrar eden keşfi ve kalabalık loglarını azaltan **14 skill ve yerel Python araçları**. Göreve gereken kodu seçer; tamamlanmış fonksiyonları, kaynak satırlarını, hata bilgisini ve gerekli doğrulamayı korur.

Python 3.8+ ve Git yeterli. Çalışan yardımcı araçlar standart kütüphane kullanır; API anahtarı, ücretli servis, embedding modeli veya ağ isteği gerektirmez. Apache-2.0 lisansı korunmuştur.

## 2.0 ile gelenler

- **Context Pack:** konu/sembol aramasından ilgili kod parçalarını sıralar; tüm çıktıyı belirtilen tahmini bağlam bütçesinde tutar. Python için AST sınırları, diğer diller için açık satır kanıtı kullanır.
- **Smart Read aracı:** satır aralığı veya tam Python sembolü okur. Bütçe yetmezse fonksiyonu sessizce kesmez. Kaynak SHA-256 ve orijinal satırlar çıktıda bulunur.
- **Diff Review:** staged, working-tree ve merge-base değişikliklerini sınırlandırılmış bir pakette verir; yeni/silinmiş dosyalar, atlanan kısımlar ve inceleme konuları görünürdür.
- **Token Budget:** içerik boyutu tahminini kullanıcı tarafından sağlanan gerçek kullanım sayılarından ayrı tutar. Kod/prompt kaydetmeden yerel kullanım günlüğü tutar.
- **Kontrollü kurulum:** minimal/balanced/full profilleri, manifest, çakışma koruması, yedekli `--force`, `--doctor`, dry-run ve yalnızca yönetilen dosyaları kaldırma. Bash ve PowerShell aynı Python kurucusunu kullanır.
- **Daha sağlam yardımcılar:** açık shell seçimi, process-tree timeout, sınırlı log okuma/yazma, eşzamanlı hafıza kilitleri, özel dosya/symlink kontrolleri, CRLF/izin koruyan toplu düzenleme ve boşluklu dosya adları.
- **Daha küçük zorunlu talimatlar:** her görevde bütün araçları çalıştırmak yerine ihtiyaç olan iş akışı seçilir. Gerekli kod/testler token tasarrufu için atlanmaz.

## Hızlı kurulum

ZIP'i açın ve paket klasöründe çalıştırın. Önce belirli bir proje seçmek kolayca gözden geçirilebilir bir kurulum sağlar:

```bash
python3 install.py --project /path/to/project --tools claude,codex --profile balanced --dry-run
python3 install.py --project /path/to/project --tools claude,codex --profile balanced
python3 install.py --project /path/to/project --tools claude,codex --doctor
```

Windows:

```powershell
.\install.ps1 -Project C:\kod\app -Tools claude,codex -Profile balanced -DryRun
.\install.ps1 -Project C:\kod\app -Tools claude,codex -Profile balanced
```

Global kurulum için `--project` kullanmayın. `./install.sh` aynı kurucuyu başlatır. `--tools` verilmezse global araçlar algılanır; proje kurulumu mevcut araç eşlemelerini seçer. `--tools all` tüm eşlemeleri açıkça seçer.

| Profil | Skill sayısı | Kullanım |
|---|---:|---|
| `minimal` | 5 | Temel protokol, ilgili kod seçimi, okuma, kısa log ve boyut/kullanım takibi |
| `balanced` | 10 | Varsayılan; harita, görev boyutlandırma, diff, test seçimi ve oturum notları eklenir |
| `full` | 14 | Kalıcı hafıza, toplu düzenleme, API sorgulama ve bağlam denetimi de eklenir |

`--skills token-saver,bulk-edit` gibi özel seçim yapılabilir; ortak yardımcıları taşıyan `token-saver` bağımlılığı otomatik eklenir. Tek skill klasörünü elle taşıyorsanız bu bağımlılığı da yanına koyun.

| Seçenek | İşlev |
|---|---|
| `--no-rules` | Yalnızca skill klasörlerini kurar |
| `--link` | Kopya yerine symlink; Windows kurulumunda kopyayı tercih edin |
| `--dry-run` | Dosya yazmadan eylemleri gösterir |
| `--doctor` | Yönetilen kopya ve kural bloklarını mevcut içerikle karşılaştırır |
| `--uninstall` | Seçili araç köklerindeki yönetilen skill'leri ve kural bloklarını kaldırır |
| `--force` | Çakışan içerikleri yedekledikten sonra değiştirir/kaldırır |

Kullanıcının aynı adlı bağımsız skill'i veya düzenlediği yönetilen içerik varsayılan olarak üzerine yazılmaz. İşaretçilerin dışındaki kurallar korunur; bozuk/çift işaretçiler hata verir. Yedekler `.token-saver-state/backups` altında kalır. Çok dosyalı kurulum tek bir dosya sistemi işlemi değildir; her başarılı adım manifest'e kaydedilir ve tekrar çalıştırılabilir.

Güncelleme: `git pull` ardından aynı kurulum komutunu çalıştırın. 1.x kurulumlarında manifest yoksa kurucu eski kopyaları otomatik sahiplenmez. Önizleyip `--force` ile yedekleyerek geçiş yapın. Kaldırırken kullanıcı tarafından sonradan değiştirilmiş içerik de korunur.

## Araç eşlemeleri

Skill keşif yolları resmi belgelerle kontrol edilmiştir; bu, uygulamaların tüm sürümlerinin bu ortamda çalıştırıldığı anlamına gelmez.

| Araç | Global / proje skill yolu | Kural yolu veya kapsam |
|---|---|---|
| Claude Code | `~/.claude/skills` / `.claude/skills` | `~/.claude/CLAUDE.md` / `CLAUDE.md` |
| Codex | `~/.agents/skills` / `.agents/skills` | `CODEX_HOME/AGENTS.md` / `AGENTS.md` |
| OpenCode | `~/.agents/skills` / `.agents/skills` | `XDG_CONFIG_HOME/opencode/AGENTS.md` / `AGENTS.md` |
| Gemini CLI | `~/.agents/skills` / `.agents/skills` | `~/.gemini/GEMINI.md` / `GEMINI.md` |
| Cursor | `~/.agents/skills` / `.agents/skills` | Global kurallar arayüzden; projede `AGENTS.md` |
| GitHub Copilot | `~/.agents/skills` / `.agents/skills` | CLI globalinde `~/.copilot/copilot-instructions.md`; projede `.github/copilot-instructions.md` |
| ZCode | Taşınabilir `.agents/skills` kopyası | Deneysel; otomatik keşif doğrulanmadı, gerekirse SKILL.md açıkça yüklenir |

Yerel/global skill'ler bulut veya uzak oturumlara her zaman otomatik aktarılmaz. İlgili aracın keşif ve uzaktan senkronizasyon belgelerini izleyin. ZCode için tam uyumluluk iddiası yoktur.

Resmi kaynaklar: [Codex](https://learn.chatgpt.com/docs/build-skills), [Claude Code](https://code.claude.com/docs/en/skills), [OpenCode](https://opencode.ai/docs/skills/), [Gemini CLI](https://geminicli.com/docs/cli/skills/), [Cursor](https://prod.cursor.com/docs/skills), [Copilot skills](https://docs.github.com/en/copilot/concepts/agents/about-agent-skills), [Copilot CLI talimatları](https://docs.github.com/en/copilot/how-tos/copilot-cli/customize-copilot/add-custom-instructions).

## Yerel araçlar

Komutları **hedef projenin içinde** çalıştırın. Aşağıdaki `TS_SKILLS` skill klasörünü gösterir; klasör adı farklıysa gerçek kurulum yolunu kullanın.

```bash
TS_SKILLS="$HOME/.agents/skills"
TS_TOOLKIT="$TS_SKILLS/token-saver/scripts/token_saver.py"

python3 "$TS_TOOLKIT" pack "refresh token expiration" --path src/ --budget 2000
python3 "$TS_TOOLKIT" read src/auth.py --symbol TokenService.refresh --budget 3000
python3 "$TS_TOOLKIT" read src/auth.ts --start 120 --end 190 --json
python3 "$TS_TOOLKIT" diff --staged --budget 2500
python3 "$TS_TOOLKIT" diff --base main --path src/ --json
python3 "$TS_TOOLKIT" budget estimate docs/design.md --json
python3 "$TS_TOOLKIT" budget record --label auth-fix --input-tokens 8200 --output-tokens 630 --cached-input-tokens 4000
python3 "$TS_TOOLKIT" budget report --json

python3 "$TS_SKILLS/repo-map/scripts/repomap.py" find Router
python3 "$TS_SKILLS/quiet-run/scripts/quiet_run.py" --lines 40 --timeout 120 -- python3 -m unittest discover -s tests
python3 "$TS_SKILLS/test-impact/scripts/affected_tests.py" --json
```

Full profilindeki ek araçlar:

```bash
python3 "$TS_SKILLS/persistent-memory/scripts/memory.py" recall "auth test"
python3 "$TS_SKILLS/persistent-memory/scripts/memory.py" add "Auth tests: pytest -q tests/test_auth.py" --kind cmd --files tests/test_auth.py
python3 "$TS_SKILLS/bulk-edit/scripts/bulk_replace.py" oldName newName --fixed --word --glob '*.py' --path src/
python3 "$TS_SKILLS/context-audit/scripts/context_audit.py" --json
```

`bulk_replace` varsayılan olarak yalnızca önizler; uygulamak için `--apply` eklenir. Shell ifadeleri `quiet_run --shell "..."` ile açıkça seçilir. Windows batch komutlarında `--shell` gerekebilir; normal argümanlar otomatik shell'e çevrilmez.

`.token-saver.json` ile yerel tarama/bütçe ayarları yapılabilir; [örnek yapılandırma](examples/retrieval-config.json) ve [ayrıntılı referans](skills/token-saver/references/configuration.md) vardır. [İş akışı referansı](skills/token-saver/references/workflows.md) kapsam ve kurtarma davranışını açıklar.

## Skill kataloğu

| Skill | Görev |
|---|---|
| token-saver | Gerekli kanıt ve doğrulamayı koruyan temel çalışma döngüsü |
| task-triage | Kapsama/riske göre süreç seçimi |
| repo-map | Artımlı, çok dilli sembol haritası |
| smart-read | Tam ilgili kod aralığını okuma |
| context-pack | Sıralanmış ve bütçeli görev bağlamı |
| diff-review | Değişiklik kapsamı ve sınırlı diff kanıtı |
| quiet-run | Hata odaklı kısa çıktı ve saklanan loglar |
| test-impact | Sezgisel odak test önerileri ve kapsam sınırları |
| session-memory | Uzun görevlerde kısa checkpoint |
| persistent-memory | Aranabilir, dosya hash'ine bağlı kalıcı bilgi |
| token-budget | İçerik boyutu tahmini ve bildirilen kullanım günlüğü |
| bulk-edit | Önizlemeli, kapsamı belirli mekanik düzenleme |
| api-lookup | Kurulu sürüm ve tam API tanımı kontrolü |
| context-audit | Talimat/skill/MCP envanteri ve olası bağlam yükü |

## Doğrulama ve ölçüm

```bash
python3 tools/validate_skills.py
python3 -m unittest discover -s tests -q
python3 benchmarks/benchmark.py
```

Testler geçici Git projeleri kullanır: bütçe/Unicode sınırları, doğru satırlar, AST gövdeleri, kaynak değişimi, staged/unstaged/yeni/silinmiş dosyalar, bozuk ref'ler, anahtar maskeleme, symlink kaçışları, eşzamanlı günlük yazma, kurulum çakışmaları, idempotence, CRLF ve güvenli kaldırma. Ağ/API harcaması yoktur. PowerShell testi çalışma zamanı varsa koşar; yoksa atlama açıkça raporlanır. CI Linux, Windows ve macOS için Python sürüm matrisi içerir.

[Örnek ölçüm](benchmarks/results.json) tekrar üretilebilir **sentetik içerik boyutu** karşılaştırmasıdır:

| Örnek | Ham içerik | Seçilen çıktı | Korunan kanıt |
|---|---:|---:|---|
| 41 kaynak dosyası, 4.000 alakasız fonksiyon | 306.308 bayt | 622 bayt | Hedef fonksiyonun tamamı |
| 2.003 satırlık başarısız test logu | 32.968 bayt | 4 satır | Hata ve başarısızlık özeti; exit=3 |

Bütün kodu okumakla bir hedef fonksiyonu seçmek farklı keşif stratejileridir; tablo aynı kalitedeki gerçek görevlerin API faturası kıyaslaması değildir. UTF-8 bayt/4 ve karakter/4 hesapları yaklaşık boyutlardır. Toplam gerçek tasarrufu değerlendirmek için aynı görev/model/ayarlarla başarıyı, tekrarları ve gözlenen kullanım sayılarını karşılaştırın.

Test önerileri doğrudan ad/import ilişkilerinden çıkarılır; dolaylı/dinamik bağımlılıkları kaçırabilir. Sembol haritası derleyici/LSP yerine geçmez. Kaynaklarda gizli değerlerin yaygın biçimleri maskelenir, fakat kapsamlı secret scan garantisi verilmez. Yeni proje hafızası yerel tutulur; mevcut paylaşım/ignore tercihleri korunur.

## Sürüm paketi

Temiz ve kaydedilmiş kaynak için:

```bash
python3 tools/package_release.py --output /path/to/Token-Saver-Skills-2.0.0.zip
```

ZIP deterministik zaman damgaları, kaynak izinleri ve her dosya için SHA-256 içeren `RELEASE-MANIFEST.json` taşır. Yanında arşiv checksum'u oluşturulur. Git verileri, önbellekler, çalışma logları ve credential dosyaları pakete alınmaz.

## English

Portable, offline coding-agent skills with ranked context packets, complete Python AST reads, bounded diff evidence, controlled installation and local usage accounting. Choose minimal/balanced/full instead of loading every workflow. Estimates are not exact/billed tokens; focused test selection and multi-language maps are heuristic. Preserve required evidence, project checks and unrelated changes. Install with `python3 install.py`; test with standard-library unittest.
