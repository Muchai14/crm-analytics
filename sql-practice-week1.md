# SQL 面试练习 Week 1：用你自己的 CRM 数据练手

配合今晚定的学习节奏：每天 30 分钟，SQL 面试题优先。这 8 道题覆盖今晚清单里的四个考点——窗口函数、CTE、自连接、日期处理——全部用你本地 `crm_analytics.duckdb` 里的真实数据（3000 leads / 1500 opportunities），每道题的答案都在你这台机器上跑通过。

**怎么跑**（30 秒）：
```bash
cd ~/workspace/projects/crm-analytics
.venv/bin/python -c "
import duckdb
con = duckdb.connect('crm_analytics.duckdb', read_only=True)
print(con.execute('''<把 SQL 粘这里>''').fetchall())
"
```

建议分两次做完（每次 ~30 分钟）：Day 1 做 Q1–Q4，Day 2 做 Q5–Q8。先自己写，卡住了再看答案。答案后的"考官在看什么"是每题的面试考察点。

---

## Day 1：窗口函数 + CTE

### Q1 — 各渠道转化最快的 3 条 Lead（窗口函数 + 日期运算）
**场景**：老板想知道每个获客渠道（lead_source）里，从创建到转化用时最短的 3 条 lead。
**答案**：
```sql
SELECT lead_source, lead_id, lead_name, owner,
       converted_date - created_date AS days_to_convert,
       ROW_NUMBER() OVER (PARTITION BY lead_source ORDER BY (converted_date - created_date)) AS speed_rank
FROM stg_leads
WHERE status = 'Converted'
QUALIFY speed_rank <= 3
ORDER BY lead_source, speed_rank;
```
预期：7 个渠道 × 3 = 21 行。例如 Event 渠道最快的是 LEAD-00882（3 天）。
**考官在看什么**：PARTITION BY 分组排名、ROW_NUMBER vs RANK 的区别（并列时要不要跳号）、DuckDB 的 QUALIFY 写法。

### Q2 — 每个销售手里的在途商机占比（窗口聚合）
**场景**：算每位 owner 的 open pipeline 金额，以及占全公司在途总额的百分比。
**答案**：
```sql
WITH open_pipe AS (
  SELECT owner, SUM(amount) AS open_amount
  FROM stg_opportunities
  WHERE stage NOT IN ('Closed Won', 'Closed Lost')
  GROUP BY owner
)
SELECT owner, open_amount,
       ROUND(100.0 * open_amount / SUM(open_amount) OVER (), 1) AS pct_of_total
FROM open_pipe
ORDER BY open_amount DESC;
```
预期：Lucas Meyer 25.7M 占 15.7%，前 5 名占了约 66%。
**考官在看什么**：`SUM() OVER ()` 全表汇总当分母、窗口函数和 GROUP BY 的执行顺序（为什么这里先 CTE 聚合再开窗）。

### Q3 — 漏斗四阶段（链式 CTE）
**场景**：一行输出 leads 创建 → leads 转化 → opportunities → closed won 四个数字。
**答案**：
```sql
WITH leads_c AS (SELECT COUNT(*) n FROM stg_leads),
     conv    AS (SELECT COUNT(*) n FROM stg_leads WHERE status = 'Converted'),
     opps    AS (SELECT COUNT(*) n FROM stg_opportunities),
     won     AS (SELECT COUNT(*) n FROM stg_opportunities WHERE stage = 'Closed Won')
SELECT 'leads_created' AS step, (SELECT n FROM leads_c) AS cnt UNION ALL
SELECT 'leads_converted', (SELECT n FROM conv) UNION ALL
SELECT 'opportunities',   (SELECT n FROM opps) UNION ALL
SELECT 'closed_won',      (SELECT n FROM won);
```
预期：3000 / 734 / 1500 / 259。
**考官在看什么**：多个 CTE 的组织方式、UNION ALL 拼结果集、能不能一眼看出漏斗转化率（734/3000 ≈ 24%）。

### Q4 — 各 segment 的 3 个月滚动赢单金额（滑动窗口）
**场景**：按 segment 和月份统计 Closed Won 金额，再算 3 个月滚动合计。
**答案**：
```sql
WITH monthly_won AS (
  SELECT segment, DATE_TRUNC('month', close_date) AS m, SUM(amount) AS won_amount
  FROM stg_opportunities
  WHERE stage = 'Closed Won'
  GROUP BY segment, m
)
SELECT segment, m, won_amount,
       SUM(won_amount) OVER (
         PARTITION BY segment ORDER BY m
         ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ) AS rolling_3m
FROM monthly_won
ORDER BY segment, m;
```
预期：Enterprise 2024-07 起 592,268，滚动 3 个月到 2024-12 为 1,645,872。
**考官在看什么**：ROWS BETWEEN 帧定义的精确含义、RANGE 和 ROWS 的区别、为什么 ORDER BY 在窗口里是必须的。

---

## Day 2：自连接 + 日期处理

### Q5 — 复购客户 Top 5（自连接找"一个客户赢过不止一次"）
**场景**：找出赢过 2 单以上的客户，按赢单数排序。
**答案**：
```sql
WITH repeat_accounts AS (
  SELECT o1.account_id
  FROM stg_opportunities o1
  JOIN stg_opportunities o2
    ON o1.account_id = o2.account_id
   AND o1.opportunity_id < o2.opportunity_id   -- 同一客户的两单，避免自己连自己、避免重复计数
  WHERE o1.stage = 'Closed Won' AND o2.stage = 'Closed Won'
  GROUP BY o1.account_id
)
SELECT a.account_name, COUNT(*) AS won_deals, SUM(o.amount) AS total_won
FROM repeat_accounts r
JOIN stg_opportunities o ON o.account_id = r.account_id AND o.stage = 'Closed Won'
JOIN stg_accounts a      ON a.account_id = r.account_id
GROUP BY a.account_name
ORDER BY won_deals DESC
LIMIT 5;
```
预期：Morton-Chase 5 单 / 1.26M 第一。
**考官在看什么**：自连接的 ON 条件为什么要加 `<`（不等连接去重）、先用自连接筛出"复购客户"再聚合的两步思路。

### Q6 — 7 天内有跟进的商机（自连接 + 日期差）
**场景**：找出某次活动之后 7 天内又有跟进动作的商机。
**答案**：
```sql
SELECT a1.what_id, a1.activity_date AS first_act, a2.activity_date AS followup,
       a2.activity_date - a1.activity_date AS days_between
FROM stg_activities a1
JOIN stg_activities a2
  ON a1.what_id = a2.what_id
 AND a2.activity_date > a1.activity_date
WHERE a1.what_type = 'Opportunity' AND a2.what_type = 'Opportunity'
  AND (a2.activity_date - a1.activity_date) <= 7
LIMIT 5;
```
预期：如 OPP-00003 在 2026-03-21 会议后 5 天（03-26）有跟进。
**考官在看什么**：自连接配不等条件、日期相减的写法、注意同一 what_id 可能产生多对组合（要不要去重）。

### Q7 — 商机创建金额的 MoM 环比（LAG）
**场景**：按月统计新创建商机金额，算环比增长率。
**答案**：
```sql
WITH m AS (
  SELECT DATE_TRUNC('month', created_date) AS m, SUM(amount) AS created_amount
  FROM stg_opportunities
  GROUP BY m
)
SELECT m, created_amount,
       LAG(created_amount) OVER (ORDER BY m) AS prev_month,
       ROUND(100.0 * (created_amount - LAG(created_amount) OVER (ORDER BY m))
             / LAG(created_amount) OVER (ORDER BY m), 1) AS mom_pct
FROM m
ORDER BY m;
```
预期：2024-02 环比 +13.7%，2024-03 环比 -42.1%。
**考官在看什么**：LAG 取上一行、NULL 的处理（第一个月没有环比）、百分比公式的括号位置。

### Q8 — 各渠道 Q1 的获客效率（季度字符串转日期）
**场景**：`stg_marketing_spend.quarter` 是 '2024-Q1' 这种字符串，把它和 leads 的创建日期对上，算每 10 万美元花费带来多少转化 lead。
**答案**：
```sql
WITH conv_q AS (
  SELECT STRFTIME('%Y', created_date) || '-Q' || ((EXTRACT(month FROM created_date) - 1) / 3 + 1)::INT AS q,
         COUNT(*) AS converted_leads
  FROM stg_leads
  WHERE status = 'Converted'
  GROUP BY 1
)
SELECT s.lead_source, s.quarter, s.spend_amount, c.converted_leads,
       ROUND(1.0 * c.converted_leads / NULLIF(s.spend_amount, 0) * 100000, 2) AS leads_per_100k
FROM stg_marketing_spend s
LEFT JOIN conv_q c ON c.q = s.quarter
WHERE s.quarter = '2024-Q1'
ORDER BY leads_per_100k DESC;
```
预期：Referral 每 10 万美元 58.15 个转化 lead，效率最高；Paid Search 只有 5.51。
**考官在看什么**：从日期推季度编号的整数运算、字符串拼接做 join key、NULLIF 防除零。

---

全部 8 道答案已在 `crm_analytics.duckdb` 上实测通过（2026-10-10）。做完之后可以顺手想想：这些查询里哪些逻辑值得沉淀成 dbt model——这就是今晚计划里"用 CRM 项目吃透 dbt"的第二步。
