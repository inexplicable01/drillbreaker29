import matplotlib.pyplot as plt
from io import BytesIO
import io
from datetime import datetime, timedelta
import base64

def createPriceChangevsDays2PendingPlot(soldhomes, savefilepath=None):
    plt.figure()
    colors = ['grey', 'olive',  'magenta']  # Example colors for 1-5 bedrooms
    for brieflisting in soldhomes:
        # print('home_type',brieflisting.homeType)
        # brieflisting.updateListingLength(listresults)
        if brieflisting.pricedelta is not None and brieflisting.list2penddays is not None:
            if brieflisting.list2penddays > 300:
                continue
            # days_to_pending.append(brieflisting.list2penddays)
            # bedrooms.append(round(brieflisting.bedrooms))
            if brieflisting.bedrooms is None:
                continue
            if round(brieflisting.bedrooms) > 3:
                color = 'purple'
            else:
                color = colors[round(brieflisting.bedrooms)-1]
            if (brieflisting.price-brieflisting.listprice)>600000.0:
                print(brieflisting)
                continue
            # if (brieflisting.price-brieflisting.listprice)==0:
            #     print(brieflisting)
            #     continue
            # Use price to determine the size of the marker
            size = (brieflisting.price / 3000000.0) * 30 +24
            if size > 174:
                size = 174
            plt.scatter(brieflisting.list2penddays, brieflisting.pricedelta, c=color, s=size)
    # Creating the plot

    plt.title('Price Change vs. Days to Pending')
    plt.xlabel('Days to Pending')
    plt.ylabel('Price Change ($)')
    for i, color in enumerate(colors):
        plt.scatter([], [], c=color, label=f'{i + 1} Bedrooms')
    plt.scatter([], [], c='purple', label='>4 Bedrooms')
    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, title='Bedroom Count')
    plt.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    plt.minorticks_on()
    plt.grid(which='minor', linestyle=':', linewidth='0.5', color='lightgray')

    # Saving the plot to a bytes buffer
    buf = BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)

    if savefilepath:
        plt.savefig(savefilepath, format='png', dpi=300)

    return base64.b64encode(buf.read()).decode('utf-8')

def createPricevsDays2PendingPlot(soldhomes, savefig=False):
    plt.figure()
    colors = ['blue', 'yellow',  'magenta']  # Example colors for 1-5 bedrooms
    for brieflisting in soldhomes:
        # print('home_type',brieflisting.homeType)
        if brieflisting.pricedelta is not None and brieflisting.list2penddays is not None:
            if brieflisting.list2penddays > 300:
                continue
            # days_to_pending.append(brieflisting.list2penddays)
            # bedrooms.append(round(brieflisting.bedrooms))
            if brieflisting.bedrooms is None:
                continue
            if round(brieflisting.bedrooms) > 3:
                color = 'purple'
            else:
                color = colors[round(brieflisting.bedrooms)-1]
            if abs(brieflisting.price-brieflisting.listprice)>600000.0:
                print(brieflisting)
                continue

            # Use price to determine the size of the marker
            size = (brieflisting.price / 3000000.0) * 30 +24
            if size > 174:
                size = 174
            plt.scatter(brieflisting.list2penddays, brieflisting.price, c=color, s=size)
    # Creating the plot

    plt.title('Price  vs. Days to Pending')
    plt.xlabel('Days to Pending')
    plt.ylabel('Price')
    for i, color in enumerate(colors):
        plt.scatter([], [], c=color, label=f'{i + 1} Bedrooms')
    plt.scatter([], [], c='purple', label='>4 Bedrooms')
    plt.legend(scatterpoints=1, frameon=False, labelspacing=1, title='Bedroom Count')

    # Saving the plot to a bytes buffer
    buf2 = BytesIO()
    plt.savefig(buf2, format='png')
    buf2.seek(0)

    return base64.b64encode(buf2.read()).decode('utf-8')

def createBarGraph(results, ylabel, title):
    data = {(year, month): count for year, month, count in results}
    # Unpack data
    today = datetime.now()
    months = [i for i in range(1, 13)]
    year1 = today.year - 2 if today.month < 12 else today.year - 1
    year2 = year1 + 1
    year3 = year2 + 1

    # Y-values for both years
    counts_year1 = [data.get((year1, m), 0) for m in months]
    counts_year2 = [data.get((year2, m), 0) for m in months]
    counts_year3 = [data.get((year3, m), 0) for m in months]

    # Labels: Jan, Feb, ...
    month_labels = [datetime(2000, m, 1).strftime("%b") for m in months]

    # Plot using Matplotlib
    x = range(len(months))
    width = 0.25

    fig, ax = plt.subplots(figsize=(8, 4))
    ax.bar([i - width for i in x], counts_year1, width=width, label=str(year1), color='skyblue')
    ax.bar([i for i in x], counts_year2, width=width, label=str(year2), color='salmon')
    ax.bar([i + width for i in x], counts_year3, width=width, label=str(year3), color='green')

    ax.set_xticks(x)
    ax.set_xticklabels(month_labels)
    ax.set_xlabel("Month")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.legend()
    # Add grid lines
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    plt.tight_layout()

    # Convert to base64 image
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    plt.close(fig)
    return chart_data

def createBarGraphWeekly(results, ylabel, title):
    # Get current year
    current_year = datetime.now().year

    # Filter results to only include current year
    filtered_data = [(year, week, count) for year, week, count in results if year == current_year]

    # Convert to dict
    data = {(year, week): count for year, week, count in filtered_data}

    # Sort weeks
    sorted_keys = sorted(data.keys())  # (year, week)
    x_labels = [f"W{week:02d}" for _, week in sorted_keys]
    y_values = [data[(year, week)] for year, week in sorted_keys]

    # Plot using Matplotlib
    fig, ax = plt.subplots(figsize=(max(10, len(x_labels) * 0.3), 4))
    ax.bar(range(len(x_labels)), y_values, width=0.6, color='skyblue')

    # Axis labels and title
    ax.set_xticks(range(len(x_labels)))
    ax.set_xticklabels(x_labels, rotation=90, fontsize=8)
    ax.set_xlabel(f"Weeks of {current_year}")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    ax.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)

    plt.tight_layout()

    # Convert to base64 image
    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    chart_data = base64.b64encode(buf.getvalue()).decode()
    buf.close()
    plt.close(fig)
    return chart_data

