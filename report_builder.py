# ceo_report_fixed.py
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from pathlib import Path
from matplotlib.backends.backend_pdf import PdfPages
import warnings
warnings.filterwarnings('ignore')

# ============================================================================
# PERSIAN TEXT SUPPORT - FIXED
# ============================================================================

try:
    import arabic_reshaper
    from bidi.algorithm import get_display
    PERSIAN_SUPPORT = True
except ImportError:
    PERSIAN_SUPPORT = False
    print("Warning: Install arabic-reshaper and python-bidi for Persian support")
    print("pip install -i https://pypi.sharif.edu/simple arabic-reshaper python-bidi")

def fa(text):
    """Convert Persian text to readable format - FIXED VERSION"""
    if not PERSIAN_SUPPORT or text is None:
        return str(text)
    try:
        # Handle non-string inputs
        text_str = str(text)
        # Reshape Arabic/Persian characters
        reshaped = arabic_reshaper.reshape(text_str)
        # Fix bidirectional text
        return get_display(reshaped)
    except Exception as e:
        return str(text)

# ============================================================================
# CONFIGURATION
# ============================================================================

OUTPUT_DIR = Path("ceo_report")
CHARTS_DIR = OUTPUT_DIR / "charts"
OUTPUT_DIR.mkdir(exist_ok=True)
CHARTS_DIR.mkdir(exist_ok=True)

# Professional color palette
COLORS = {
    'primary': '#1B4965',
    'secondary': '#00B4D8',
    'success': '#06D6A0',
    'danger': '#EF476F',
    'warning': '#FFD166',
    'dark': '#0B132B',
    'light': '#F8F9FA',
    'gray': '#6C757D'
}

# Set matplotlib style
plt.style.use('seaborn-v0_8-whitegrid')
sns.set_palette("Set2")

# Set font for Persian support
if PERSIAN_SUPPORT:
    try:
        plt.rcParams['font.family'] = 'Tahoma'
    except:
        pass

# ============================================================================
# LOAD DATA
# ============================================================================

def load_data():
    """Load your actual data here."""
    np.random.seed(42)
    dates = pd.date_range('2023-01-01', '2025-05-31', freq='D')
    n = len(dates)
    
    df = pd.DataFrame({
        'Date': dates,
        'Revenue': np.random.normal(50000, 10000, n).cumsum() / 10 + 100000,
        'Profit': np.random.normal(10000, 2000, n).cumsum() / 10 + 20000,
        'Orders': np.random.poisson(200, n).cumsum() // 5,
        'Customers': np.random.poisson(150, n).cumsum() // 10,
        'Region': np.random.choice(['Tehran', 'Mashhad', 'Isfahan', 'Shiraz', 'Tabriz'], n, p=[0.35, 0.25, 0.15, 0.15, 0.10]),
        'Product': np.random.choice(['Product_A', 'Product_B', 'Product_C', 'Product_D'], n, p=[0.35, 0.30, 0.20, 0.15])
    })
    
    df['Profit_Margin'] = (df['Profit'] / df['Revenue'] * 100).round(2)
    
    # Add missing values
    for col in ['Revenue', 'Profit', 'Orders']:
        idx = np.random.choice(df.index, size=int(len(df) * 0.03), replace=False)
        df.loc[idx, col] = np.nan
    
    return df

df = load_data()
df['Date'] = pd.to_datetime(df['Date'])
df['YearMonth'] = df['Date'].dt.strftime('%Y-%m')
df['Year'] = df['Date'].dt.year
df['Month'] = df['Date'].dt.month

# ============================================================================
# CEO ANALYSIS
# ============================================================================

def analyze_performance(df):
    """Analyze performance and answer CEO questions."""
    
    # Current vs previous month comparison
    months = sorted(df['YearMonth'].unique())
    current_month = months[-1] if len(months) > 0 else None
    prev_month = months[-2] if len(months) > 1 else None
    
    current_data = df[df['YearMonth'] == current_month] if current_month else pd.DataFrame()
    prev_data = df[df['YearMonth'] == prev_month] if prev_month else pd.DataFrame()
    
    if not current_data.empty and not prev_data.empty:
        revenue_growth = ((current_data['Revenue'].sum() - prev_data['Revenue'].sum()) / prev_data['Revenue'].sum() * 100) if prev_data['Revenue'].sum() > 0 else 0
        profit_growth = ((current_data['Profit'].sum() - prev_data['Profit'].sum()) / prev_data['Profit'].sum() * 100) if prev_data['Profit'].sum() > 0 else 0
        orders_growth = ((current_data['Orders'].sum() - prev_data['Orders'].sum()) / prev_data['Orders'].sum() * 100) if prev_data['Orders'].sum() > 0 else 0
    else:
        revenue_growth = profit_growth = orders_growth = 0
    
    # Region performance
    region_perf = df.groupby('Region').agg({
        'Revenue': 'sum',
        'Profit': 'sum',
        'Orders': 'count'
    }).round(2)
    region_perf['Profit_Margin'] = (region_perf['Profit'] / region_perf['Revenue'] * 100).round(2)
    region_perf = region_perf.sort_values('Revenue', ascending=False)
    
    # Product performance
    product_perf = df.groupby('Product').agg({
        'Revenue': 'sum',
        'Profit': 'sum',
        'Orders': 'count'
    }).round(2)
    product_perf['Profit_Margin'] = (product_perf['Profit'] / product_perf['Revenue'] * 100).round(2)
    product_perf = product_perf.sort_values('Profit_Margin', ascending=False)
    
    # Monthly revenue for peak analysis
    monthly_rev = df.groupby('YearMonth')['Revenue'].sum()
    peak_month = monthly_rev.idxmax() if not monthly_rev.empty else None
    peak_revenue = monthly_rev.max() if not monthly_rev.empty else 0
    current_revenue = monthly_rev[current_month] if current_month and current_month in monthly_rev.index else 0
    gap_to_peak = ((peak_revenue - current_revenue) / peak_revenue * 100) if peak_revenue > 0 else 0
    
    # Determine focus area
    worst_region = region_perf.index[-1] if len(region_perf) > 0 else None
    worst_product = product_perf.index[-1] if len(product_perf) > 0 else None
    avg_margin = df['Profit_Margin'].mean()
    
    if worst_region and region_perf.loc[worst_region, 'Profit_Margin'] < avg_margin:
        focus = f"Improve {worst_region} region performance"
    elif worst_product:
        focus = f"Review {worst_product} product pricing/margin"
    else:
        focus = "Maintain current growth trajectory"
    
    # Overall status
    if revenue_growth > 5 and profit_growth > 5:
        overall_status = "EXCELLENT"
        status_color = COLORS['success']
    elif revenue_growth > 0 and profit_growth > 0:
        overall_status = "GOOD"
        status_color = COLORS['secondary']
    elif revenue_growth > 0:
        overall_status = "WARNING"
        status_color = COLORS['warning']
    else:
        overall_status = "CRITICAL"
        status_color = COLORS['danger']
    
    return {
        'current_month': current_month,
        'prev_month': prev_month,
        'revenue_growth': revenue_growth,
        'profit_growth': profit_growth,
        'orders_growth': orders_growth,
        'region_perf': region_perf,
        'product_perf': product_perf,
        'best_region': region_perf.index[0] if len(region_perf) > 0 else None,
        'worst_region': worst_region,
        'best_product': product_perf.index[0] if len(product_perf) > 0 else None,
        'worst_product': worst_product,
        'peak_month': peak_month,
        'peak_revenue': peak_revenue,
        'current_revenue': current_revenue,
        'gap_to_peak': gap_to_peak,
        'focus': focus,
        'overall_status': overall_status,
        'status_color': status_color
    }

# ============================================================================
# PROFESSIONAL CHARTS
# ============================================================================

def create_revenue_trend_chart(df, analysis):
    """Create revenue trend chart with peak highlight."""
    monthly = df.groupby('YearMonth')['Revenue'].sum().reset_index()
    
    fig, ax = plt.subplots(figsize=(14, 6), facecolor='white')
    ax.set_facecolor(COLORS['light'])
    
    x = range(len(monthly))
    y = monthly['Revenue'].values / 1e9
    
    # Line with area fill
    ax.plot(x, y, color=COLORS['primary'], linewidth=2.5, marker='o', markersize=6)
    ax.fill_between(x, y, alpha=0.2, color=COLORS['primary'])
    
    # Highlight peak point
    peak_idx = monthly['Revenue'].idxmax()
    ax.scatter(peak_idx, y[peak_idx], s=200, color=COLORS['success'], 
               edgecolors='white', linewidth=2, zorder=5)
    ax.annotate('PEAK', xy=(peak_idx, y[peak_idx]), xytext=(10, 10),
                textcoords='offset points', fontsize=10, fontweight='bold',
                color=COLORS['success'], bbox=dict(boxstyle='round,pad=0.2', facecolor='white'))
    
    # Highlight current point
    current_idx = len(monthly) - 1
    ax.scatter(current_idx, y[current_idx], s=150, color=COLORS['warning'],
               edgecolors='white', linewidth=2, zorder=5)
    
    # Draw gap line if needed
    if peak_idx != current_idx:
        ax.annotate('', xy=(current_idx, y[current_idx]), xytext=(peak_idx, y[peak_idx]),
                    arrowprops=dict(arrowstyle='<->', color=COLORS['danger'], lw=2))
        
        mid_x = (peak_idx + current_idx) / 2
        mid_y = (y[peak_idx] + y[current_idx]) / 2
        ax.text(mid_x, mid_y, f"Gap: {analysis['gap_to_peak']:.1f}%", 
                ha='center', va='bottom', fontsize=11, fontweight='bold',
                color=COLORS['danger'], bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8))
    
    # Labels
    ax.set_title('Monthly Revenue Trend Analysis', fontsize=16, fontweight='bold', pad=20, color=COLORS['dark'])
    ax.set_xlabel('Month', fontsize=12, color=COLORS['gray'])
    ax.set_ylabel('Revenue (Billion Toman)', fontsize=12, color=COLORS['gray'])
    ax.grid(True, alpha=0.3, linestyle='--')
    
    # X-axis ticks (show every 3 months)
    step = max(1, len(monthly) // 10)
    ax.set_xticks(range(0, len(monthly), step))
    ax.set_xticklabels([monthly['YearMonth'].iloc[i] for i in range(0, len(monthly), step)], rotation=45, ha='right')
    
    # Add value labels on points
    for i, (xi, yi) in enumerate(zip(x, y)):
        if i % step == 0 or i == peak_idx or i == current_idx:
            ax.annotate(f'{yi:.1f}B', xy=(xi, yi), xytext=(0, 10),
                        textcoords='offset points', ha='center', fontsize=8, alpha=0.7)
    
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '01_revenue_trend.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return CHARTS_DIR / '01_revenue_trend.png'


def create_region_performance_chart(df, analysis):
    """Create region performance comparison chart."""
    region = analysis['region_perf']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')
    
    # Revenue by region
    regions = list(region.index)
    revenues = (region['Revenue'] / 1e9).values
    colors_rev = [COLORS['danger'] if i == len(regions)-1 else COLORS['primary'] for i in range(len(regions))]
    
    bars1 = ax1.barh(regions, revenues, color=colors_rev)
    ax1.set_xlabel('Revenue (Billion Toman)', fontsize=11)
    ax1.set_title('Revenue by Region', fontsize=13, fontweight='bold')
    
    for bar, val in zip(bars1, revenues):
        ax1.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}B', va='center', fontsize=10)
    
    # Profit margin by region
    margins = region['Profit_Margin'].values
    colors_margin = [COLORS['danger'] if m < analysis['region_perf']['Profit_Margin'].mean() else COLORS['success'] for m in margins]
    
    bars2 = ax2.barh(regions, margins, color=colors_margin)
    ax2.set_xlabel('Profit Margin (%)', fontsize=11)
    ax2.set_title('Profit Margin by Region', fontsize=13, fontweight='bold')
    ax2.axvline(analysis['region_perf']['Profit_Margin'].mean(), color=COLORS['gray'], 
                linestyle='--', label='Company Average')
    
    for bar, val in zip(bars2, margins):
        ax2.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}%', va='center', fontsize=10)
    
    ax2.legend(loc='lower right')
    
    plt.suptitle('Regional Performance Analysis', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '02_region_performance.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return CHARTS_DIR / '02_region_performance.png'


def create_product_performance_chart(df, analysis):
    """Create product performance comparison chart."""
    product = analysis['product_perf']
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor='white')
    
    # Revenue by product
    products = list(product.index)
    revenues = (product['Revenue'] / 1e9).values
    
    bars1 = ax1.bar(products, revenues, color=COLORS['primary'])
    ax1.set_ylabel('Revenue (Billion Toman)', fontsize=11)
    ax1.set_title('Revenue by Product', fontsize=13, fontweight='bold')
    ax1.tick_params(axis='x', rotation=45)
    
    for bar, val in zip(bars1, revenues):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                f'{val:.1f}B', ha='center', va='bottom', fontsize=10)
    
    # Profit margin by product
    margins = product['Profit_Margin'].values
    colors_margin = [COLORS['success'] if m >= product['Profit_Margin'].mean() else COLORS['danger'] for m in margins]
    
    bars2 = ax2.bar(products, margins, color=colors_margin)
    ax2.set_ylabel('Profit Margin (%)', fontsize=11)
    ax2.set_title('Profit Margin by Product', fontsize=13, fontweight='bold')
    ax2.axhline(product['Profit_Margin'].mean(), color=COLORS['gray'], 
                linestyle='--', label='Company Average')
    ax2.tick_params(axis='x', rotation=45)
    
    for bar, val in zip(bars2, margins):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5,
                f'{val:.1f}%', ha='center', va='bottom', fontsize=10)
    
    ax2.legend(loc='upper right')
    
    plt.suptitle('Product Performance Analysis', fontsize=14, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '03_product_performance.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return CHARTS_DIR / '03_product_performance.png'


def create_gap_analysis_chart(df, analysis):
    """Create gap analysis chart."""
    monthly = df.groupby('YearMonth')['Revenue'].sum()
    
    fig, ax = plt.subplots(figsize=(12, 6), facecolor='white')
    ax.set_facecolor(COLORS['light'])
    
    months = range(len(monthly))
    values = monthly.values / 1e9
    
    # Area chart
    ax.fill_between(months, values, alpha=0.3, color=COLORS['primary'])
    ax.plot(months, values, linewidth=2.5, color=COLORS['primary'], marker='o', markersize=6)
    
    # Highlight peak
    peak_idx = values.argmax()
    ax.scatter(peak_idx, values[peak_idx], s=200, color=COLORS['success'], 
               edgecolors='white', linewidth=2, zorder=5)
    ax.annotate(f"Best Month\n{analysis['peak_month']}", xy=(peak_idx, values[peak_idx]),
                xytext=(10, 10), textcoords='offset points', fontsize=10,
                bbox=dict(boxstyle='round,pad=0.3', facecolor='white', edgecolor=COLORS['success']))
    
    # Highlight current
    current_idx = len(values) - 1
    ax.scatter(current_idx, values[current_idx], s=150, color=COLORS['warning'],
               edgecolors='white', linewidth=2, zorder=5)
    
    # Gap annotation
    ax.annotate('', xy=(current_idx, values[current_idx]), xytext=(peak_idx, values[peak_idx]),
                arrowprops=dict(arrowstyle='<->', color=COLORS['danger'], lw=2))
    
    mid_idx = (peak_idx + current_idx) / 2
    mid_val = (values[peak_idx] + values[current_idx]) / 2
    ax.text(mid_idx, mid_val, f"Gap to Peak\n{analysis['gap_to_peak']:.1f}%", 
            ha='center', va='bottom', fontsize=12, fontweight='bold',
            color=COLORS['danger'], bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9))
    
    ax.set_title('Distance to Historical Peak', fontsize=16, fontweight='bold', pad=20, color=COLORS['dark'])
    ax.set_xlabel('Month', fontsize=12, color=COLORS['gray'])
    ax.set_ylabel('Revenue (Billion Toman)', fontsize=12, color=COLORS['gray'])
    ax.grid(True, alpha=0.3, linestyle='--')
    
    step = max(1, len(monthly) // 8)
    ax.set_xticks(range(0, len(monthly), step))
    ax.set_xticklabels([monthly.index[i] for i in range(0, len(monthly), step)], rotation=45, ha='right')
    
    plt.tight_layout()
    plt.savefig(CHARTS_DIR / '04_gap_analysis.png', dpi=200, bbox_inches='tight', facecolor='white')
    plt.close()
    return CHARTS_DIR / '04_gap_analysis.png'

# ============================================================================
# EXCEL REPORT (ENGLISH COLUMN NAMES TO AVOID ENCODING ISSUES)
# ============================================================================

def create_excel_report(df, analysis):
    """Create Excel report with English column names."""
    excel_path = OUTPUT_DIR / "ceo_report.xlsx"
    
    with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
        # Executive Summary
        exec_data = {
            'Metric': [
                'Overall Status',
                'Revenue Growth (vs last month)',
                'Profit Growth (vs last month)',
                'Orders Growth (vs last month)',
                'Best Region',
                'Worst Region',
                'Best Product',
                'Worst Product',
                'Peak Month',
                'Current Revenue (Billion)',
                'Peak Revenue (Billion)',
                'Gap to Peak (%)',
                'Focus Area'
            ],
            'Value': [
                analysis['overall_status'],
                f"{analysis['revenue_growth']:+.1f}%",
                f"{analysis['profit_growth']:+.1f}%",
                f"{analysis['orders_growth']:+.1f}%",
                analysis['best_region'],
                analysis['worst_region'],
                analysis['best_product'],
                analysis['worst_product'],
                analysis['peak_month'],
                f"{analysis['current_revenue']/1e9:.2f}",
                f"{analysis['peak_revenue']/1e9:.2f}",
                f"{analysis['gap_to_peak']:.1f}%",
                analysis['focus']
            ]
        }
        pd.DataFrame(exec_data).to_excel(writer, sheet_name='Executive Summary', index=False)
        
        # Monthly Performance
        monthly = df.groupby('YearMonth').agg({
            'Revenue': 'sum',
            'Profit': 'sum',
            'Orders': 'count'
        }).round(2)
        monthly.columns = ['Revenue', 'Profit', 'Orders']
        monthly.to_excel(writer, sheet_name='Monthly Performance')
        
        # Region Performance
        region = analysis['region_perf'].copy()
        region.columns = ['Revenue', 'Profit', 'Orders', 'Profit_Margin']
        region.to_excel(writer, sheet_name='Region Performance')
        
        # Product Performance
        product = analysis['product_perf'].copy()
        product.columns = ['Revenue', 'Profit', 'Orders', 'Profit_Margin']
        product.to_excel(writer, sheet_name='Product Performance')
    
    return excel_path

# ============================================================================
# PROFESSIONAL PDF REPORT
# ============================================================================

def create_pdf_report(analysis, chart_files):
    """Create professional PDF report with proper layout."""
    pdf_path = OUTPUT_DIR / "ceo_report.pdf"
    
    with PdfPages(pdf_path) as pdf:
        # Page 1: Cover Page
        fig = plt.figure(figsize=(11, 8.5), facecolor='white')
        ax = fig.add_subplot(111)
        ax.axis('off')
        
        # Title
        ax.text(0.5, 0.75, 'CEO EXECUTIVE REPORT', transform=ax.transAxes,
                fontsize=28, fontweight='bold', ha='center', color=COLORS['dark'])
        ax.text(0.5, 0.65, 'Business Performance Dashboard', transform=ax.transAxes,
                fontsize=16, ha='center', color=COLORS['gray'])
        
        # Date
        ax.text(0.5, 0.55, f'Report Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}', 
                transform=ax.transAxes, fontsize=12, ha='center', color=COLORS['gray'])
        
        # Status box
        status_box = dict(boxstyle='round,pad=0.5', facecolor=analysis['status_color'], alpha=0.8)
        ax.text(0.5, 0.42, f"STATUS: {analysis['overall_status']}", transform=ax.transAxes,
                fontsize=18, fontweight='bold', ha='center', color='white', bbox=status_box)
        
        # Key metrics in 4 boxes
        metrics = [
            (f"Revenue Growth", f"{analysis['revenue_growth']:+.1f}%"),
            (f"Profit Growth", f"{analysis['profit_growth']:+.1f}%"),
            (f"Orders Growth", f"{analysis['orders_growth']:+.1f}%"),
            (f"Gap to Peak", f"{analysis['gap_to_peak']:.1f}%")
        ]
        
        box_y = 0.28
        for i, (label, value) in enumerate(metrics):
            x_pos = 0.2 + (i * 0.2)
            color = COLORS['success'] if '+' in value else COLORS['danger'] if '-' in value else COLORS['warning']
            
            bbox = dict(boxstyle='round,pad=0.3', facecolor=COLORS['light'], edgecolor=color, linewidth=2)
            ax.text(x_pos, box_y, label, transform=ax.transAxes, fontsize=10, ha='center', color=COLORS['gray'])
            ax.text(x_pos, box_y - 0.05, value, transform=ax.transAxes, fontsize=16, fontweight='bold', 
                    ha='center', color=color, bbox=bbox)
        
        # Footer
        ax.text(0.5, 0.05, 'Confidential - Management Use Only', transform=ax.transAxes,
                fontsize=9, ha='center', color=COLORS['gray'])
        
        pdf.savefig(fig, dpi=150)
        plt.close()
        
        # Page 2: Executive Summary Table
        fig, ax = plt.subplots(figsize=(11, 8.5), facecolor='white')
        ax.axis('off')
        
        ax.text(0.05, 0.95, 'Executive Summary', transform=ax.transAxes,
                fontsize=20, fontweight='bold', color=COLORS['dark'])
        
        # Create table
        table_data = [
            ['Metric', 'Value'],
            ['Overall Status', analysis['overall_status']],
            ['Revenue Growth', f"{analysis['revenue_growth']:+.1f}%"],
            ['Profit Growth', f"{analysis['profit_growth']:+.1f}%"],
            ['Orders Growth', f"{analysis['orders_growth']:+.1f}%"],
            ['Best Region', analysis['best_region']],
            ['Worst Region', analysis['worst_region']],
            ['Best Product', analysis['best_product']],
            ['Worst Product', analysis['worst_product']],
            ['Peak Month', analysis['peak_month']],
            ['Gap to Peak', f"{analysis['gap_to_peak']:.1f}%"],
            ['Focus Area', analysis['focus']]
        ]
        
        table = ax.table(cellText=table_data, loc='center', cellLoc='left', colWidths=[0.35, 0.55])
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        table.scale(1.2, 1.5)
        
        # Style header row
        for i in range(2):
            table[(0, i)].set_facecolor(COLORS['primary'])
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        pdf.savefig(fig, dpi=150)
        plt.close()
        
        # Page 3-6: Charts
        for chart_path in chart_files:
            if chart_path and chart_path.exists():
                fig = plt.figure(figsize=(11, 8.5), facecolor='white')
                img = plt.imread(chart_path)
                plt.imshow(img)
                plt.axis('off')
                pdf.savefig(fig, dpi=150)
                plt.close()
        
        # Last Page: Recommendations
        fig, ax = plt.subplots(figsize=(11, 8.5), facecolor='white')
        ax.axis('off')
        
        ax.text(0.05, 0.95, 'Strategic Recommendations', transform=ax.transAxes,
                fontsize=20, fontweight='bold', color=COLORS['dark'])
        
        recommendations = [
            f"1. Focus on {analysis['worst_region']} region - currently underperforming",
            f"2. Review {analysis['worst_product']} product pricing strategy",
            f"3. Leverage {analysis['best_region']} region as benchmark for others",
            f"4. Increase marketing spend on {analysis['best_product']}",
            f"5. Target {analysis['gap_to_peak']:.1f}% gap to reach historical peak",
            "6. Implement monthly performance review process"
        ]
        
        y_pos = 0.82
        for rec in recommendations:
            ax.text(0.1, y_pos, rec, transform=ax.transAxes, fontsize=12, color=COLORS['dark'])
            y_pos -= 0.08
        
        # Action plan box
        ax.text(0.05, 0.35, 'Immediate Action Plan', transform=ax.transAxes,
                fontsize=14, fontweight='bold', color=COLORS['success'])
        
        actions = [
            f"• Priority 1: Investigate {analysis['worst_region']} region issues",
            f"• Priority 2: Optimize {analysis['worst_product']} product margin",
            f"• Priority 3: Scale successful strategies from {analysis['best_region']}"
        ]
        
        y_pos = 0.28
        for action in actions:
            ax.text(0.1, y_pos, action, transform=ax.transAxes, fontsize=11, color=COLORS['gray'])
            y_pos -= 0.06
        
        pdf.savefig(fig, dpi=150)
        plt.close()
    
    return pdf_path

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("\n" + "="*60)
    print("CEO Executive Report Generator")
    print("="*60)
    
    # Analyze data
    print("\n Analyzing business performance...")
    analysis = analyze_performance(df)
    
    # Generate charts
    print(" Generating charts...")
    chart_files = []
    
    chart = create_revenue_trend_chart(df, analysis)
    if chart: chart_files.append(chart); print("   Revenue trend chart")
    
    chart = create_region_performance_chart(df, analysis)
    if chart: chart_files.append(chart); print("   Region performance chart")
    
    chart = create_product_performance_chart(df, analysis)
    if chart: chart_files.append(chart); print("   Product performance chart")
    
    chart = create_gap_analysis_chart(df, analysis)
    if chart: chart_files.append(chart); print("   Gap analysis chart")
    
    # Create reports
    print("\n Creating Excel report...")
    excel_path = create_excel_report(df, analysis)
    print(f"   Excel saved: {excel_path}")
    
    print(" Creating PDF report...")
    pdf_path = create_pdf_report(analysis, chart_files)
    print(f"   PDF saved: {pdf_path}")
    
    # Print summary
    print("\n" + "="*60)
    print("EXECUTIVE SUMMARY")
    print("="*60)
    print(f"Status: {analysis['overall_status']}")
    print(f"Revenue Growth: {analysis['revenue_growth']:+.1f}%")
    print(f"Profit Growth: {analysis['profit_growth']:+.1f}%")
    print(f"Best Region: {analysis['best_region']}")
    print(f"Worst Region: {analysis['worst_region']}")
    print(f"Gap to Peak: {analysis['gap_to_peak']:.1f}%")
    print(f"Focus: {analysis['focus']}")
    print("="*60)
    print(f"\n Output folder: {OUTPUT_DIR.absolute()}")
    print(f" Files: ceo_report.xlsx | ceo_report.pdf | charts/")
    print("="*60)


if __name__ == "__main__":
    main()