# AOR 模组新闻编写规则

本资料目录内的 AOR 新闻制作，以及向正式模组安装新闻时，必须遵守：

- 所有玩家可见的 `news_event` 统一写入正式模组的 `events/AOR_world_news.txt`。不要再为单条新闻、国家新闻或专题新闻新建独立事件文件。
- 使用该文件已有的新闻 namespace：`AOR_news_global`、`AOR_news_europe`、`AOR_news_asia`、`AOR_news_africa`、`AOR_news_oceania`、`AOR_news_north_america`、`AOR_news_south_america`。根据新闻覆盖范围选择，不要自行另建新闻 namespace。
- 新增新闻前，扫描正式模组中所选 namespace 的全部事件 ID，使用该 namespace 当前最大数字加 1；编号必须唯一，保留旧编号，不重排或复用已有编号。
- 本地化统一写入对应语言的 `localisation/<语言>/AOR_world_news_l_<语言>.yml`，沿用事件编号，如 `.t`、`.desc`、`.a` 等；不要将新闻文本散放在项目或科技本地化中。保持本地化文件的 UTF-8 BOM。
- 配图在 `interface/AOR_world_news_pictures.gfx` 注册，图片名和 sprite 名对应事件编号，例如 `GFX_AOR_news_global.6_pic`；DDS 放入 `gfx/event_pictures/AOR_news/`。
- 全球重大新闻使用 `AOR_news_global.<编号>`，按现有全球重大新闻设置 `major = yes`，让所有玩家可见，不加地区订阅限制。地区新闻沿用现有地区订阅和路由机制。
- `events/AOR_news_router.txt` 可以保留或新增隐藏分发事件，但玩家可见的新闻正文必须留在 `AOR_world_news.txt`。项目、国策、决议等来源只负责触发对应 ID，修改 ID 时同步更新所有引用。
- 交付前检查编号唯一、触发引用、本地化键和图片引用一致。此规则适用于以后新增或修改的新闻，不授权无关的大规模迁移。

正式模组目前位于 `C:\Users\DONG\Documents\Paradox Interactive\Hearts of Iron IV\mod\new-aor`。以正式模组当前文件为准，不要拿资料目录中的旧成品覆盖较新的文件。

- 新闻标题本地化必须以 `[Get_AOR_news_masthead]` 开头，例如 `AOR_news_global.6.t:0 "[Get_AOR_news_masthead]粒子加速器的建成"`。现有界面依赖此前缀显示报头并定位标题，缺失会导致报头消失且标题移出可见区域。检查标题时必须验证此前缀。
