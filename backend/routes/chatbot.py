"""
Chatbot — Natural language interface to the dw_pi database.
Understands questions about sales, customers, products, anomalies, promotions.
No external AI API needed — uses keyword matching + real SQL queries.
"""

import warnings
warnings.filterwarnings('ignore')

import re
import io
import os
import pandas as pd
from flask import Blueprint, jsonify, request
from db import query_df

chatbot_bp = Blueprint('chatbot', __name__)

# ─────────────────────────────────────────────────────────────────────────────
# Intent detection helpers
# ─────────────────────────────────────────────────────────────────────────────

def _normalize(text: str) -> str:
    return text.lower().strip()

def _contains(text: str, *keywords) -> bool:
    return any(k in text for k in keywords)

def _extract_number(text: str, default=None):
    m = re.search(r'\b(\d+)\b', text)
    return int(m.group(1)) if m else default

def _extract_month(text: str):
    months = {
        'january': 1, 'february': 2, 'march': 3, 'april': 4,
        'may': 5, 'june': 6, 'july': 7, 'august': 8,
        'september': 9, 'october': 10, 'november': 11, 'december': 12,
        'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'jun': 6,
        'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
    }
    for name, num in months.items():
        if name in text:
            return num, name.capitalize()
    return None, None

# ─────────────────────────────────────────────────────────────────────────────
# Query handlers — each returns a dict with { answer, data?, type }
# ─────────────────────────────────────────────────────────────────────────────

def handle_total_sales(q: str) -> dict:
    month_num, month_name = _extract_month(q)
    year = _extract_number(q)

    if month_num and year and year > 1000:
        sql = f"""
            SELECT SUM(s.total_price) as total, COUNT(*) as transactions
            FROM fact_sale s
            INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
            WHERE d.month = {month_num} AND d.year = {year}
        """
        df = query_df(sql)
        total = df['total'].iloc[0] or 0
        txn   = df['transactions'].iloc[0] or 0
        return {
            'answer': f"In {month_name} {year}, total sales were **{total:,.0f} DT** across **{txn:,} transactions**.",
            'type': 'stat'
        }
    elif month_num:
        sql = f"""
            SELECT d.year, SUM(s.total_price) as total, COUNT(*) as transactions
            FROM fact_sale s
            INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
            WHERE d.month = {month_num}
            GROUP BY d.year ORDER BY d.year DESC
        """
        df = query_df(sql)
        if df.empty:
            return {'answer': f"No sales data found for {month_name}.", 'type': 'empty'}
        rows = [f"• {int(r.year)}: {r.total:,.0f} DT ({int(r.transactions):,} transactions)" for _, r in df.iterrows()]
        return {
            'answer': f"Sales in **{month_name}** by year:\n" + "\n".join(rows),
            'type': 'list'
        }
    else:
        sql = """
            SELECT SUM(total_price) as total, COUNT(*) as transactions,
                   AVG(total_price) as avg_sale
            FROM fact_sale
        """
        df = query_df(sql)
        total = df['total'].iloc[0] or 0
        txn   = df['transactions'].iloc[0] or 0
        avg   = df['avg_sale'].iloc[0] or 0
        return {
            'answer': f"Overall database totals:\n• **Total Revenue:** {total:,.0f} DT\n• **Total Transactions:** {txn:,}\n• **Average Sale Value:** {avg:,.2f} DT",
            'type': 'stat'
        }


def handle_top_products(q: str) -> dict:
    n = _extract_number(q, 5)
    n = min(n, 20)
    sql = f"""
        SELECT TOP {n} p.name_product, c.name_category,
               SUM(s.quantity) as total_qty,
               SUM(s.total_price) as total_revenue
        FROM fact_sale s
        INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
        INNER JOIN dim_category c ON p.fk_category = c.pk_id_category
        GROUP BY p.name_product, c.name_category
        ORDER BY total_revenue DESC
    """
    df = query_df(sql)
    if df.empty:
        return {'answer': "No product data found.", 'type': 'empty'}
    rows = [f"**{i+1}. {r.name_product}** ({r.name_category}) — {r.total_revenue:,.0f} DT | {int(r.total_qty):,} units"
            for i, (_, r) in enumerate(df.iterrows())]
    return {
        'answer': f"Top {n} products by revenue:\n" + "\n".join(rows),
        'type': 'list',
        'table': df.rename(columns={'name_product': 'Product', 'name_category': 'Category',
                                     'total_qty': 'Units Sold', 'total_revenue': 'Revenue (DT)'}).to_dict(orient='records')
    }


def handle_top_customers(q: str) -> dict:
    n = _extract_number(q, 5)
    n = min(n, 20)
    sql_b2b = f"""
        SELECT TOP {n} b.company as name, 'B2B' as type,
               COUNT(*) as orders, SUM(s.total_price) as revenue
        FROM fact_sale s
        INNER JOIN dim_clientb2b b ON s.fk_clientB2B = b.pk_id_client
        GROUP BY b.company ORDER BY revenue DESC
    """
    sql_b2c = f"""
        SELECT TOP {n} CONCAT(b.first_name, ' ', b.last_name) as name, 'B2C' as type,
               COUNT(*) as orders, SUM(s.total_price) as revenue
        FROM fact_sale s
        INNER JOIN dim_clientb2c b ON s.fk_clientB2C = b.pk_id_client
        GROUP BY b.first_name, b.last_name ORDER BY revenue DESC
    """
    try:
        df_b2b = query_df(sql_b2b)
        df_b2c = query_df(sql_b2c)
        df = pd.concat([df_b2b, df_b2c]).sort_values('revenue', ascending=False).head(n)
    except Exception:
        df = query_df(sql_b2b)

    if df.empty:
        return {'answer': "No customer data found.", 'type': 'empty'}
    rows = [f"**{i+1}. {r['name']}** ({r['type']}) — {r['revenue']:,.0f} DT | {int(r['orders']):,} orders"
            for i, (_, r) in enumerate(df.iterrows())]
    return {
        'answer': f"Top {n} customers by revenue:\n" + "\n".join(rows),
        'type': 'list',
        'table': df.rename(columns={'name': 'Customer', 'type': 'Type',
                                     'orders': 'Orders', 'revenue': 'Revenue (DT)'}).to_dict(orient='records')
    }


def handle_categories(q: str) -> dict:
    sql = """
        SELECT c.name_category,
               COUNT(DISTINCT p.pk_id_product) as products,
               SUM(s.quantity) as total_qty,
               SUM(s.total_price) as total_revenue
        FROM fact_sale s
        INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
        INNER JOIN dim_category c ON p.fk_category = c.pk_id_category
        GROUP BY c.name_category
        ORDER BY total_revenue DESC
    """
    df = query_df(sql)
    if df.empty:
        return {'answer': "No category data found.", 'type': 'empty'}
    rows = [f"• **{r.name_category}** — {r.total_revenue:,.0f} DT | {int(r.products)} products | {int(r.total_qty):,} units"
            for _, r in df.iterrows()]
    return {
        'answer': "Sales by product category:\n" + "\n".join(rows),
        'type': 'list',
        'table': df.rename(columns={'name_category': 'Category', 'products': 'Products',
                                     'total_qty': 'Units Sold', 'total_revenue': 'Revenue (DT)'}).to_dict(orient='records')
    }


def handle_monthly_trend(q: str) -> dict:
    year = _extract_number(q)
    if year and year > 1000:
        sql = f"""
            SELECT d.month, SUM(s.total_price) as revenue, SUM(s.quantity) as qty
            FROM fact_sale s
            INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
            WHERE d.year = {year}
            GROUP BY d.month ORDER BY d.month
        """
        df = query_df(sql)
        if df.empty:
            return {'answer': f"No data found for year {year}.", 'type': 'empty'}
        month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
        rows = [f"• **{month_names[int(r.month)-1]}**: {r.revenue:,.0f} DT ({int(r.qty):,} units)"
                for _, r in df.iterrows()]
        return {
            'answer': f"Monthly sales trend for **{year}**:\n" + "\n".join(rows),
            'type': 'list'
        }
    else:
        sql = """
            SELECT d.year, d.month, SUM(s.total_price) as revenue
            FROM fact_sale s
            INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
            GROUP BY d.year, d.month
            ORDER BY d.year DESC, d.month DESC
        """
        df = query_df(sql)
        if df.empty:
            return {'answer': "No trend data found.", 'type': 'empty'}
        years = df['year'].unique()[:3]
        lines = []
        for y in sorted(years, reverse=True):
            yr_data = df[df['year'] == y]
            total = yr_data['revenue'].sum()
            lines.append(f"• **{int(y)}**: {total:,.0f} DT total")
        return {
            'answer': "Annual revenue summary (recent years):\n" + "\n".join(lines) +
                      "\n\nAsk me about a specific year (e.g. 'sales trend 2023') for monthly details.",
            'type': 'list'
        }


def handle_discounts(q: str) -> dict:
    sql = """
        SELECT AVG(discount) as avg_discount,
               MAX(discount) as max_discount,
               MIN(discount) as min_discount,
               COUNT(CASE WHEN discount > 0 THEN 1 END) as discounted_sales,
               COUNT(*) as total_sales
        FROM fact_sale
    """
    df = query_df(sql)
    r = df.iloc[0]
    pct = (r['discounted_sales'] / r['total_sales'] * 100) if r['total_sales'] > 0 else 0
    return {
        'answer': f"Discount analysis:\n• **Average Discount:** {r['avg_discount']:.1%}\n• **Max Discount:** {r['max_discount']:.1%}\n• **Discounted Sales:** {int(r['discounted_sales']):,} ({pct:.1f}% of all sales)\n• **Total Sales:** {int(r['total_sales']):,}",
        'type': 'stat'
    }


def handle_claims(q: str) -> dict:
    sql = """
        SELECT TOP 10 description, status
        FROM dim_claim
        WHERE description IS NOT NULL
        ORDER BY pk_id_claim DESC
    """
    try:
        df = query_df(sql)
        count_sql = "SELECT COUNT(*) as total FROM dim_claim"
        count_df = query_df(count_sql)
        total = int(count_df['total'].iloc[0])
        if df.empty:
            return {'answer': "No customer claims found in the database.", 'type': 'empty'}
        rows = [f"• [{r.get('status','N/A')}] {r['description'][:80]}..." if len(str(r['description'])) > 80
                else f"• [{r.get('status','N/A')}] {r['description']}"
                for _, r in df.iterrows()]
        return {
            'answer': f"There are **{total} total claims** in the database. Here are the 10 most recent:\n" + "\n".join(rows),
            'type': 'list'
        }
    except Exception as e:
        return {'answer': f"Could not retrieve claims: {str(e)}", 'type': 'error'}


def handle_product_search(q: str) -> dict:
    # Extract product name from query
    patterns = [
        r'(?:about|for|product|sales of|revenue of|how (?:is|are)|tell me about)\s+(.+?)(?:\?|$)',
        r'(.+?)\s+(?:sales|revenue|performance)',
    ]
    product_name = None
    for pat in patterns:
        m = re.search(pat, q, re.IGNORECASE)
        if m:
            candidate = m.group(1).strip()
            if len(candidate) > 2 and candidate.lower() not in ('the', 'a', 'an', 'my', 'our'):
                product_name = candidate
                break

    if not product_name:
        return None  # Signal: not a product search

    sql = f"""
        SELECT TOP 5 p.name_product, c.name_category,
               SUM(s.quantity) as total_qty,
               SUM(s.total_price) as total_revenue,
               AVG(s.unit_price) as avg_price,
               AVG(s.discount) as avg_discount
        FROM fact_sale s
        INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
        INNER JOIN dim_category c ON p.fk_category = c.pk_id_category
        WHERE p.name_product LIKE '%{product_name}%'
        GROUP BY p.name_product, c.name_category
        ORDER BY total_revenue DESC
    """
    df = query_df(sql)
    if df.empty:
        return {
            'answer': f"No product found matching **\"{product_name}\"**. Try asking for top products or a specific category.",
            'type': 'empty'
        }
    rows = []
    for _, r in df.iterrows():
        rows.append(
            f"**{r['name_product']}** ({r['name_category']})\n"
            f"  Revenue: {r['total_revenue']:,.0f} DT | Units: {int(r['total_qty']):,} | "
            f"Avg Price: {r['avg_price']:,.2f} DT | Avg Discount: {r['avg_discount']:.1%}"
        )
    return {
        'answer': f"Results for **\"{product_name}\"**:\n\n" + "\n\n".join(rows),
        'type': 'list'
    }


def handle_summary(q: str) -> dict:
    sql_sales = "SELECT COUNT(*) as txn, SUM(total_price) as rev FROM fact_sale"
    sql_prod  = "SELECT COUNT(*) as cnt FROM dim_product"
    sql_b2b   = "SELECT COUNT(*) as cnt FROM dim_clientb2b"
    sql_b2c   = "SELECT COUNT(*) as cnt FROM dim_clientb2c"
    sql_claim = "SELECT COUNT(*) as cnt FROM dim_claim"

    try:
        s = query_df(sql_sales).iloc[0]
        p = query_df(sql_prod).iloc[0]
        b2b = query_df(sql_b2b).iloc[0]
        b2c = query_df(sql_b2c).iloc[0]
        cl  = query_df(sql_claim).iloc[0]
        return {
            'answer': (
                "Here is a summary of your database:\n\n"
                f"• **Total Revenue:** {s['rev']:,.0f} DT\n"
                f"• **Total Transactions:** {int(s['txn']):,}\n"
                f"• **Products:** {int(p['cnt']):,}\n"
                f"• **B2B Customers:** {int(b2b['cnt']):,}\n"
                f"• **B2C Customers:** {int(b2c['cnt']):,}\n"
                f"• **Customer Claims:** {int(cl['cnt']):,}\n\n"
                "Ask me anything more specific — top products, monthly trends, customer performance, discounts, and more!"
            ),
            'type': 'stat'
        }
    except Exception as e:
        return {'answer': f"Could not load summary: {str(e)}", 'type': 'error'}


def handle_help() -> dict:
    return {
        'answer': (
            "I can answer questions about your **dw_pi** database. Here are some things you can ask me:\n\n"
            "**Sales & Revenue**\n"
            "• What are the total sales?\n"
            "• Show me sales for January 2023\n"
            "• What is the monthly trend for 2023?\n\n"
            "**Products**\n"
            "• What are the top 10 products?\n"
            "• Show me sales by category\n"
            "• Tell me about [product name]\n\n"
            "**Customers**\n"
            "• Who are the top 5 customers?\n"
            "• Show me the best B2B clients\n\n"
            "**Other**\n"
            "• What is the average discount?\n"
            "• Show me recent customer claims\n"
            "• Give me a database summary"
        ),
        'type': 'help'
    }


# ─────────────────────────────────────────────────────────────────────────────
# Main intent router
# ─────────────────────────────────────────────────────────────────────────────

def route_intent(q: str) -> dict:
    n = _normalize(q)

    # Greetings
    if _contains(n, 'hello', 'hi ', 'hey', 'bonjour', 'salut', 'good morning', 'good afternoon'):
        return {'answer': "Hello! I'm your Sougui data assistant. Ask me anything about your sales, products, customers, or trends. Type **help** to see what I can do.", 'type': 'greeting'}

    # Help
    if _contains(n, 'help', 'what can you', 'what do you', 'how to use', 'guide', 'commands'):
        return handle_help()

    # Summary / overview
    if _contains(n, 'summary', 'overview', 'database', 'how many', 'total number', 'give me a'):
        return handle_summary(n)

    # Monthly trend
    if _contains(n, 'trend', 'monthly', 'by month', 'per month', 'evolution', 'over time'):
        return handle_monthly_trend(n)

    # Top products
    if _contains(n, 'top product', 'best product', 'best selling', 'most sold', 'best seller', 'popular product'):
        return handle_top_products(n)

    # Categories
    if _contains(n, 'categor', 'category', 'categories', 'by category', 'product type'):
        return handle_categories(n)

    # Top customers
    if _contains(n, 'top customer', 'best customer', 'biggest client', 'top client', 'best client', 'vip'):
        return handle_top_customers(n)

    # Discounts
    if _contains(n, 'discount', 'promotion', 'promo', 'rebate', 'reduction'):
        return handle_discounts(n)

    # Claims / complaints
    if _contains(n, 'claim', 'complaint', 'feedback', 'issue', 'problem', 'réclamation'):
        return handle_claims(n)

    # Total sales / revenue
    if _contains(n, 'total sale', 'total revenue', 'revenue', 'sales', 'turnover', 'chiffre'):
        return handle_total_sales(n)

    # Product-specific search (last resort)
    result = handle_product_search(q)
    if result:
        return result

    # Fallback
    return {
        'answer': (
            "I'm not sure I understood that. Here are some things you can ask:\n\n"
            "• **Total sales** or **sales in January 2023**\n"
            "• **Top 5 products** or **top customers**\n"
            "• **Sales by category** or **monthly trend 2023**\n"
            "• **Discount analysis** or **recent claims**\n"
            "• **Database summary**\n\n"
            "Type **help** for the full list."
        ),
        'type': 'fallback'
    }


# ─────────────────────────────────────────────────────────────────────────────
# Endpoint
# ─────────────────────────────────────────────────────────────────────────────

@chatbot_bp.route('/ask', methods=['POST'])
def ask():
    try:
        body = request.get_json(force=True) or {}
        question = body.get('question', '').strip()
        if not question:
            return jsonify({'success': False, 'error': 'No question provided'}), 400

        result = route_intent(question)
        return jsonify({'success': True, **result})
    except Exception as e:
        return jsonify({
            'success': True,
            'answer': f"I encountered an error while querying the database: {str(e)}\n\nPlease check your database connection and try again.",
            'type': 'error'
        })


# ─────────────────────────────────────────────────────────────────────────────
# ✨ Summarize — full database narrative summary
# ─────────────────────────────────────────────────────────────────────────────

@chatbot_bp.route('/summarize', methods=['GET'])
def summarize():
    """Generate a rich narrative summary of the entire database."""
    try:
        # Core sales stats
        s = query_df("SELECT COUNT(*) as txn, SUM(total_price) as rev, AVG(total_price) as avg_sale, AVG(discount) as avg_disc FROM fact_sale").iloc[0]
        # Products
        p = query_df("SELECT COUNT(*) as cnt FROM dim_product").iloc[0]
        # Customers
        b2b = query_df("SELECT COUNT(*) as cnt FROM dim_clientb2b").iloc[0]
        b2c = query_df("SELECT COUNT(*) as cnt FROM dim_clientb2c").iloc[0]
        # Claims
        cl = query_df("SELECT COUNT(*) as cnt FROM dim_claim").iloc[0]
        # Top product
        top_prod = query_df("""
            SELECT TOP 1 p.name_product, SUM(s.total_price) as rev
            FROM fact_sale s
            INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
            GROUP BY p.name_product ORDER BY rev DESC
        """).iloc[0]
        # Top category
        top_cat = query_df("""
            SELECT TOP 1 c.name_category, SUM(s.total_price) as rev
            FROM fact_sale s
            INNER JOIN dim_product p ON s.fk_product = p.pk_id_product
            INNER JOIN dim_category c ON p.fk_category = c.pk_id_category
            GROUP BY c.name_category ORDER BY rev DESC
        """).iloc[0]
        # Best year
        best_year = query_df("""
            SELECT TOP 1 d.year, SUM(s.total_price) as rev
            FROM fact_sale s
            INNER JOIN dim_date d ON s.fk_date = d.pk_id_date
            GROUP BY d.year ORDER BY rev DESC
        """).iloc[0]
        # Top B2B customer
        try:
            top_b2b = query_df("""
                SELECT TOP 1 b.company, SUM(s.total_price) as rev
                FROM fact_sale s
                INNER JOIN dim_clientb2b b ON s.fk_clientB2B = b.pk_id_client
                GROUP BY b.company ORDER BY rev DESC
            """).iloc[0]
            top_b2b_name = top_b2b['company']
            top_b2b_rev  = top_b2b['rev']
        except Exception:
            top_b2b_name = 'N/A'
            top_b2b_rev  = 0

        # Discount rate
        disc_pct = float(s['avg_disc']) * 100 if s['avg_disc'] else 0

        summary = (
            f"✨ **Database Summary — dw_pi**\n\n"
            f"**Overview**\n"
            f"• Total Revenue: **{float(s['rev']):,.0f} DT** across **{int(s['txn']):,} transactions**\n"
            f"• Average Sale Value: **{float(s['avg_sale']):,.2f} DT**\n"
            f"• Average Discount Applied: **{disc_pct:.1f}%**\n\n"
            f"**Products & Categories**\n"
            f"• Catalogue: **{int(p['cnt']):,} products**\n"
            f"• Best-Selling Product: **{top_prod['name_product']}** ({float(top_prod['rev']):,.0f} DT)\n"
            f"• Top Category: **{top_cat['name_category']}** ({float(top_cat['rev']):,.0f} DT)\n\n"
            f"**Customers**\n"
            f"• B2B Clients: **{int(b2b['cnt']):,}** | B2C Clients: **{int(b2c['cnt']):,}**\n"
            f"• Top B2B Client: **{top_b2b_name}** ({float(top_b2b_rev):,.0f} DT)\n\n"
            f"**Performance**\n"
            f"• Best Year: **{int(best_year['year'])}** ({float(best_year['rev']):,.0f} DT)\n"
            f"• Customer Claims on Record: **{int(cl['cnt']):,}**\n\n"
            f"Ask me for more details on any of these areas!"
        )

        return jsonify({'success': True, 'answer': summary, 'type': 'summary'})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ─────────────────────────────────────────────────────────────────────────────
# 📎 Upload — parse PDF or CSV and return a summary
# ─────────────────────────────────────────────────────────────────────────────

def _summarize_csv(df: pd.DataFrame, filename: str) -> str:
    rows, cols = df.shape
    col_list = ", ".join(df.columns.tolist()[:10])
    if len(df.columns) > 10:
        col_list += f" ... (+{len(df.columns)-10} more)"

    lines = [
        f"📄 **File:** {filename}",
        f"• **Rows:** {rows:,} | **Columns:** {cols}",
        f"• **Columns:** {col_list}",
        ""
    ]

    # Numeric columns stats
    num_cols = df.select_dtypes(include='number').columns.tolist()
    if num_cols:
        lines.append("**Numeric Column Summary:**")
        for col in num_cols[:6]:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                continue
            lines.append(
                f"• **{col}** — Min: {col_data.min():,.2f} | Max: {col_data.max():,.2f} | "
                f"Avg: {col_data.mean():,.2f} | Total: {col_data.sum():,.2f}"
            )
        lines.append("")

    # Text columns — unique value counts
    text_cols = df.select_dtypes(include='object').columns.tolist()
    if text_cols:
        lines.append("**Text Column Insights:**")
        for col in text_cols[:4]:
            unique = df[col].nunique()
            top_val = df[col].value_counts().index[0] if unique > 0 else 'N/A'
            lines.append(f"• **{col}** — {unique} unique values | Most common: \"{top_val}\"")
        lines.append("")

    # Missing values
    missing = df.isnull().sum().sum()
    if missing > 0:
        lines.append(f"⚠️ **Missing Values:** {missing:,} cells across the dataset")
    else:
        lines.append("✅ **No missing values detected**")

    return "\n".join(lines)


def _summarize_excel(df: pd.DataFrame, filename: str, sheet_names: list) -> str:
    """Summarize a single Excel sheet, with sheet list header."""
    rows, cols = df.shape
    col_list = ", ".join(df.columns.astype(str).tolist()[:10])
    if len(df.columns) > 10:
        col_list += f" ... (+{len(df.columns)-10} more)"

    lines = [
        f"📊 **File:** {filename}",
        f"• **Sheets:** {', '.join(sheet_names)}",
        f"• **Rows:** {rows:,} | **Columns:** {cols}",
        f"• **Columns:** {col_list}",
        ""
    ]

    num_cols = df.select_dtypes(include='number').columns.tolist()
    if num_cols:
        lines.append("**Numeric Column Summary:**")
        for col in num_cols[:6]:
            col_data = df[col].dropna()
            if len(col_data) == 0:
                continue
            lines.append(
                f"• **{col}** — Min: {col_data.min():,.2f} | Max: {col_data.max():,.2f} | "
                f"Avg: {col_data.mean():,.2f} | Total: {col_data.sum():,.2f}"
            )
        lines.append("")

    text_cols = df.select_dtypes(include='object').columns.tolist()
    if text_cols:
        lines.append("**Text Column Insights:**")
        for col in text_cols[:4]:
            unique = df[col].nunique()
            top_val = df[col].value_counts().index[0] if unique > 0 else 'N/A'
            lines.append(f"• **{col}** — {unique} unique values | Most common: \"{top_val}\"")
        lines.append("")

    missing = df.isnull().sum().sum()
    lines.append(f"⚠️ **Missing Values:** {missing:,} cells" if missing > 0 else "✅ **No missing values detected**")

    return "\n".join(lines)


def _summarize_pdf(content: bytes, filename: str) -> str:
    """Extract text from PDF and produce a summary."""
    try:
        import pdfplumber
        text_chunks = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            total_pages = len(pdf.pages)
            for page in pdf.pages[:5]:  # First 5 pages
                t = page.extract_text()
                if t:
                    text_chunks.append(t.strip())

        full_text = "\n".join(text_chunks)
        word_count = len(full_text.split())
        char_count = len(full_text)

        # Extract first meaningful lines as preview
        lines = [l.strip() for l in full_text.split('\n') if len(l.strip()) > 20][:8]
        preview = "\n".join([f"• {l[:120]}..." if len(l) > 120 else f"• {l}" for l in lines])

        # Look for numbers in the text
        numbers = re.findall(r'\b\d[\d,\.]*\b', full_text)
        num_count = len(numbers)

        summary = (
            f"📄 **File:** {filename}\n"
            f"• **Pages:** {total_pages} | **Words:** {word_count:,} | **Characters:** {char_count:,}\n"
            f"• **Numbers/Values found:** {num_count:,}\n\n"
            f"**Content Preview (first {min(total_pages,5)} pages):**\n"
            f"{preview if preview else 'No readable text found in this PDF.'}\n\n"
            f"💡 Tip: For deeper analysis, export your PDF data as CSV and upload again."
        )
        return summary

    except ImportError:
        # pdfplumber not installed — basic fallback
        return (
            f"📄 **File:** {filename}\n"
            f"• PDF uploaded successfully ({len(content):,} bytes)\n\n"
            f"⚠️ To enable full PDF text extraction, install **pdfplumber**:\n"
            f"`pip install pdfplumber`\n\n"
            f"For now, try uploading a **CSV file** for a detailed analysis."
        )
    except Exception as e:
        return f"📄 **File:** {filename}\n\nCould not parse PDF: {str(e)}"


@chatbot_bp.route('/upload', methods=['POST'])
def upload_file():
    """Accept a PDF, CSV, or Excel file and return a summary."""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        filename = file.filename or 'unknown'
        ext = os.path.splitext(filename)[1].lower()
        content = file.read()

        if ext == '.csv':
            for enc in ['utf-8', 'latin-1', 'cp1252']:
                try:
                    df = pd.read_csv(io.BytesIO(content), encoding=enc)
                    break
                except Exception:
                    continue
            else:
                return jsonify({'success': False, 'error': 'Could not decode CSV file. Try saving it as UTF-8.'}), 400
            answer = _summarize_csv(df, filename)

        elif ext in ('.xlsx', '.xls'):
            try:
                # Read all sheets
                xl = pd.ExcelFile(io.BytesIO(content))
                sheet_names = xl.sheet_names
                if len(sheet_names) == 1:
                    df = xl.parse(sheet_names[0])
                    answer = _summarize_excel(df, filename, sheet_names)
                else:
                    # Summarize each sheet
                    parts = [f"📊 **File:** {filename} — **{len(sheet_names)} sheets:** {', '.join(sheet_names)}\n"]
                    for name in sheet_names[:5]:  # max 5 sheets
                        try:
                            df = xl.parse(name)
                            parts.append(f"---\n**Sheet: {name}**")
                            parts.append(_summarize_csv(df, name))
                        except Exception:
                            parts.append(f"**Sheet: {name}** — could not be parsed")
                    answer = "\n".join(parts)
            except ImportError:
                return jsonify({'success': False, 'error': 'openpyxl is required for Excel files. Run: pip install openpyxl'}), 400

        elif ext == '.pdf':
            answer = _summarize_pdf(content, filename)

        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported file type "{ext}". Please upload a CSV, Excel (.xlsx/.xls), or PDF file.'
            }), 400

        return jsonify({'success': True, 'answer': answer, 'type': 'file_summary', 'filename': filename})

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
