from django.shortcuts import render
from django.db.models import Count, Case, When, IntegerField, Min, Max
from django.db.models.functions import TruncMonth
from arrestdashboard.models import ArrestRecord
import pandas as pd
import plotly.express as px
from datetime import datetime
from plotly.express import Constant



import plotly.graph_objects as go

def get_chart_html(fig):
    if fig is None or not fig.data:
        # create a blank figure
        fig = go.Figure()
        fig.update_layout(
            xaxis=dict(showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showgrid=False, zeroline=False, visible=False),
            plot_bgcolor="white",
            paper_bgcolor="white",
            margin=dict(l=20, r=20, t=20, b=20)
        )
    return fig.to_html(full_html=False, include_plotlyjs='cdn', config={'displayModeBar': False})

def dashboard(request):
    fig_line = None
    fig_bar_month = None
    # --- Get filters from request ---
    selected_state = request.GET.get('state', 'All')
    selected_composition = request.GET.get('composition', 'All')
    selected_age_group = request.GET.get('age_group', 'All')
    selected_nationality = request.GET.get('nationality_group','All')
    from_date = request.GET.get('from_date', '')
    to_date = request.GET.get('to_date', '')

    # --- Base queryset ---
    qs = ArrestRecord.objects.all()
    Grand_Total_Arrests = qs.count()
    dates = qs.aggregate(
    first_date=Min("apprehension_date"),
    last_date=Max("apprehension_date")
    )
    first_date = dates["first_date"]
    last_date = dates["last_date"]
    # Apply state filter
    if selected_state != 'All':
        qs = qs.filter(apprehension_state__iexact=selected_state)

    if selected_age_group != 'All':
        qs = qs.filter(age_category__iexact=selected_age_group)
    
    if selected_nationality != 'All':
        qs = qs.filter(citizenship_country__iexact = selected_nationality)

    # Apply timeline filter
    
    if from_date:
        try:
            from_date_parsed = datetime.strptime(from_date, '%Y-%m-%d').date()
            qs = qs.filter(apprehension_date__gte=from_date_parsed)
        except ValueError:
            pass

    if to_date:
        try:
            to_date_parsed = datetime.strptime(to_date, '%Y-%m-%d').date()
            qs = qs.filter(apprehension_date__lte=to_date_parsed)
        except ValueError:
            pass

    total_arrests = qs.count()

    # --- State counts chart ---
    state_counts_qs = qs.values('apprehension_state') \
                        .annotate(count=Count('id')) \
                        .order_by('-count')
    state_counts = pd.DataFrame(list(state_counts_qs))
    if not state_counts.empty:
        state_counts = state_counts.rename(columns={'apprehension_state': 'state'})
        fig_bar_state = px.bar(state_counts, x='state', y='count', color='state', 
                               title='Arrests by State')
        fig_bar_state.update_layout(xaxis_title='State', yaxis_title='Number of Arrests')
        chart_bar_state = fig_bar_state.to_html(full_html=False, include_plotlyjs='cdn',
                                               config={'displayModeBar': False})
    else:
        chart_bar_state = "<p>No data available for state chart</p>"

    # --- Monthly trends ---
    monthly_counts_qs = qs.annotate(month=TruncMonth('apprehension_date')) \
                          .values('month') \
                          .annotate(count=Count('id')) \
                          .order_by('month')
    monthly_counts = pd.DataFrame(list(monthly_counts_qs))
    if not monthly_counts.empty:
        monthly_counts['month'] = pd.to_datetime(monthly_counts['month'])
    else:
        monthly_counts = pd.DataFrame(columns=['month', 'count'])

    # --- Composition charts ---
################### Gender Composition Chart ######################
    if selected_composition == "Gender":
        comp_qs = qs.exclude(gender='Unknown')\
                    .values('gender') \
                    .annotate(month=TruncMonth('apprehension_date')) \
                    .values('month', 'gender') \
                    .annotate(count=Count('id')) \
                    .order_by('month')
        comp_df = pd.DataFrame(list(comp_qs))
        if not comp_df.empty:
            comp_df['month'] = pd.to_datetime(comp_df['month'])
            comp_df['percent'] = comp_df.groupby('month')['count'].transform(lambda x: 100 * x / x.sum()).round(2)

            fig_line = px.line(comp_df, x='month', y='count', color='gender',color_discrete_sequence = ['#4FA3E0', '#87CEEB'], markers=False,
                            category_orders={'gender': ['Male','Female']},  # Order of stacks
                            labels={'month':'Year-Month','count':'Number of arrests','gender':'Gender','percent':'% of monthly total'},
                            title=f"Monthly Arrests by Gender ({selected_state})")
            fig_line.update_traces(
                line=dict(width=5, shape='spline', smoothing=0.3),  # 0 = linear, 1 = very smooth
                marker=dict(size=7)
            )

            fig_line.update_layout(
                xaxis=dict(
                            tickformat='%b%Y',
                            title='Year-Month',
                            tickmode='array',
                            tickvals=comp_df['month'],   # replace with your x-axis column
                            ticktext=[d.strftime('%b%Y') for d in comp_df['month']]
                        ),
                yaxis=dict(tickformat=',',title='Number of Arrests'),
                plot_bgcolor='rgba(173, 216, 230, 0.15)',   # very light transparent blue
                paper_bgcolor='rgba(173, 216, 230, 0.2)',
                legend=dict(x=0.05,y=1,bgcolor='rgba(173,216,230,0.2)'),
                margin=dict(l=40, r=40, t=80, b=40)
            )
            comp_df['bar_label'] = comp_df['count'].apply(lambda x: f"{x:,}")
            comp_df['percent_str'] = comp_df['percent'].apply(lambda x: f"{x:.1f}%")
            fig_bar_month = px.bar(
                comp_df,
                x='month',
                y='count',
                color='gender',
                color_discrete_sequence = ['#4FA3E0', '#87CEEB'],
                text='bar_label',
                hover_data={
                    'count': True,
                    'percent_str': True,
                    'month': True,
                    'gender': True,
                    'bar_label':False
                },
                category_orders={'gender': ['Male','Female']},  # Order of stacks
                labels={'month':'Year-Month','count':'Number of arrests','gender':'Gender','percent_str':'% of monthly total'},
                title=f"Monthly Arrests by Gender ({selected_state})"
            )
            fig_bar_month.update_layout(
                barmode='stack',
                # xaxis=dict(tickformat='%b%Y',title='Year-Month'),
                xaxis=dict(
                            tickformat='%b%Y',
                            title='Year-Month',
                            tickmode='array',
                            tickvals=comp_df['month'],   # replace with your x-axis column
                            ticktext=[d.strftime('%b%Y') for d in comp_df['month']]
                        ),
                # xaxis=dict(
                #     tickformat='%b%Y',
                #     title='Year-Month',
                #     tickangle=45,   # rotate labels to fit more
                #     nticks=len(comp_df)  # suggest max number of ticks
                # ),
                yaxis=dict(tickformat=',',title='Number of Arrests'),
                legend=dict(x=0.05,y=1,bgcolor='rgba(173,216,230,0.2)'),
                uniformtext_minsize=10,
                uniformtext_mode='hide',
                # height = 800,
                plot_bgcolor='rgba(173, 216, 230, 0.15)',   # very light transparent blue
                paper_bgcolor='rgba(173, 216, 230, 0.2)'   # even lighter for paper

            )
############################  Criminality Composition ##################################
    elif selected_composition == "Criminality":
        comp_qs = qs.values('apprehension_criminality') \
                    .annotate(month=TruncMonth('apprehension_date')) \
                    .values('month', 'apprehension_criminality') \
                    .annotate(count=Count('id')) \
                    .order_by('month')
        comp_df = pd.DataFrame(list(comp_qs))
        if not comp_df.empty:
            comp_df['month'] = pd.to_datetime(comp_df['month'])
            
            # Calculate percentage per month for hover
            comp_df['percent'] = comp_df.groupby('month')['count'].transform(lambda x: 100 * x / x.sum()).round(2)

            # fig_line = px.line(comp_df, x='month', y='count', color='apprehension_criminality', markers=True,
            #                 title=f"Monthly Arrests by Criminality ({selected_state})")
            # fig_line.update_layout(
            #     plot_bgcolor="#f4efe1",      # chart area background
            #     paper_bgcolor='white',                 # match CSS container height
            #     margin=dict(l=40, r=40, t=80, b=40),  # optional margins
            # )
            fig_line = px.line(
                comp_df,
                x='month',
                y='count',
                color='apprehension_criminality',
                color_discrete_sequence = ['#1F77B4', '#4FA3E0', '#87CEEB'],
                markers=False,
                category_orders={'apprehension_criminality':['1 Convicted Criminal','2 Pending Criminal Charges','3 Other Immigration Violator']},
                labels={'month':'Year-Month','count':'Number of arrests','apprehension_criminality':'Criminality','percent':'% per month'},
                title=f"Monthly Arrests by Criminality ({selected_state})",
                line_shape='spline'  # smooth line
            )

            # Adjust the smoothing factor
            fig_line.update_traces(
                line=dict(width=4, shape='spline', smoothing=0.3),  # 0 = linear, 1 = very smooth
                marker=dict(size=7)
            )
            comp_df['bar_label'] = comp_df['count'].apply(lambda x: f"{x:,}")
            comp_df['percent_str'] = comp_df['percent'].apply(lambda x: f"{x:.1f}%")
            fig_line.update_layout(
                xaxis=dict(tickformat='%b%Y',
                            title='Year-Month',
                            tickmode='array',
                            tickvals=comp_df['month'],   # replace with your x-axis column
                            ticktext=[d.strftime('%b%Y') for d in comp_df['month']]
                        ),
                yaxis=dict(tickformat=',',title='Number of Arrests'),
                plot_bgcolor='rgba(173, 216, 230, 0.15)',   # very light transparent blue
                paper_bgcolor='rgba(173, 216, 230, 0.2)',
                legend=dict(x=0.05,y=1,bgcolor='rgba(173,216,230,0.2)'),
                margin=dict(l=40, r=40, t=80, b=40)
            )
            # Bar chart with hover showing count + percentage
            fig_bar_month = px.bar(
                comp_df,
                x='month',
                y='count',
                color='apprehension_criminality',
                color_discrete_sequence = ['#1F77B4', '#4FA3E0', '#87CEEB'],
                # color_continuous_scale="Blues",
                text='bar_label',
                hover_data={
                    'count': True,
                    'percent_str':True,
                    'month': True,
                    'apprehension_criminality': True,
                    'bar_label':False
                },
                category_orders={'apprehension_criminality':['1 Convicted Criminal','2 Pending Criminal Charges','3 Other Immigration Violator']},
                labels={'month':'Year-Month','count':'Number of arrests','apprehension_criminality':'Criminality','percent_str':'% of monthly total'},
                title=f"Monthly Arrests by Criminality ({selected_state})"
            )
            fig_bar_month.update_layout(barmode='stack',
                                        xaxis=dict(
                                        tickformat='%b%Y',
                                        title='Year-Month',
                                        tickmode='array',
                                        tickvals=comp_df['month'],   # replace with your x-axis column
                                        ticktext=[d.strftime('%b%Y') for d in comp_df['month']]
                                    ),
                                        yaxis=dict(tickformat=',',title='Number of Arrests'),
                                        legend=dict(x=0.05,y=1,bgcolor='rgba(173,216,230,0.2)'),
                                        uniformtext_minsize=10,
                                        uniformtext_mode='hide',
                                        # height = 800,
                                        plot_bgcolor='rgba(173, 216, 230, 0.15)',   # very light transparent blue
                                        paper_bgcolor='rgba(173, 216, 230, 0.2)'
                                        )

    else:
        # Default monthly trend chart
        # comp_qs = qs.annotate(month=TruncMonth('apprehension_date'))\
        #             .values('month')\
        #             .annotate(count=Count('id'))\
        #             .order_by('month')
        # comp_df = pd.DataFrame(list(comp_qs))
        # comp_qs = qs.annotate(month=TruncMonth('apprehension_date'))\
        #                          .values('month')\
        #                          .annotate(count=Count('id'))\
        #                          .order_by('month')
        # monthly_counts = pd.DataFrame(list(comp_qs))
        if not monthly_counts.empty:
            fig_line = px.line(monthly_counts, x='month', y='count', markers=False,color_discrete_sequence=['#4FA3E0'],
                               labels={'month':'Year-Month','count':'Number of arrests'},
                            title=f"Monthly Arrests Over Time ({selected_state})")
            fig_line.update_traces(
                line=dict(width=4, shape='spline', smoothing=0.3),  # 0 = linear, 1 = very smooth
                marker=dict(size=1)
            )
            
            #if annotation is requured
            # fig_line.update_traces(
            #     line=dict(width=4, shape='spline', smoothing=0.3),
            #     marker=dict(size=6, color='#4FA3E0'),
            #     textposition="top center",  # <-- controls where text shows
            #     textfont=dict(size=12)      # <-- adjust font size
            #     )
            # fig_line.update_traces(
            #     textposition="top center",
            #     textfont=dict(size=12),
            #     texttemplate="%{text}",  # use text column
            # )

            # # small shift upwards to keep away from line
            # for t in fig_line.data:
            #     t.textposition = "top center"
            #     t.textfont = dict(size=12)
            #     t.text = t.text  # keeps the text
            fig_line.update_layout(
                xaxis=dict(tickformat='%b%Y',
                            title='Year-Month',
                            tickmode='array',
                            tickvals=monthly_counts['month'],
                            ticktext=[d.strftime('%b%Y') for d in monthly_counts['month']]),
                yaxis=dict(tickformat=',',title='Number of Arrests'),
                plot_bgcolor='rgba(173, 216, 230, 0.15)',   # very light transparent blue
                paper_bgcolor='rgba(173, 216, 230, 0.2)',
                legend=dict(x=0.05,y=1,bgcolor='rgba(173,216,230,0.2)'),
                margin=dict(l=40, r=40, t=80, b=40)
            )
            monthly_counts['bar_label'] = monthly_counts['count'].apply(lambda x: f"{x:,}")
            fig_bar_month = px.bar(monthly_counts, x='month', y='count', text='bar_label',
                                hover_data={
                                    'count':True,
                                    'month':True,
                                    'bar_label':False
                                },
                                color_discrete_sequence=['#4FA3E0'],
                                labels={'month':'Year-Month','count':'Number of arrests'},
                                title=f"Monthly Arrests Bar Chart ({selected_state})")
            fig_bar_month.update_layout(barmode='stack',
                                            xaxis=dict(
                                            tickformat='%b%Y',
                                            title='Year-Month',
                                            tickmode='array',
                                            tickvals=monthly_counts['month'],
                                            ticktext=[d.strftime('%b%Y') for d in monthly_counts['month']]),
                                            yaxis=dict(tickformat=',',title='Number of Arrests'),
                                            legend=dict(x=0.05,y=1,bgcolor='rgba(173,216,230,0.2)'),
                                            uniformtext_minsize=10,
                                            uniformtext_mode='hide',
                                            # height = 800,
                                            plot_bgcolor='rgba(173, 216, 230, 0.15)',   # very light transparent blue
                                            paper_bgcolor='rgba(173, 216, 230, 0.2)'
                                            )

    # Convert charts to HTML
    # chart_line = fig_line.to_html(full_html=False, include_plotlyjs='cdn',
    #                             config={'displayModeBar': False})
    # chart_bar_month = fig_bar_month.to_html(full_html=False, include_plotlyjs='cdn',
    #                                     config={'displayModeBar': False})
    
    chart_line = get_chart_html(fig_line)
    chart_bar_month = get_chart_html(fig_bar_month)

    
##################### Maps visualization ############################################

    # --- State abbreviations for map ---
    state_abbrev = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "Florida": "FL", "Georgia": "GA", "Hawaii": "HI", "Idaho": "ID",
    "Illinois": "IL", "Indiana": "IN", "Iowa": "IA", "Kansas": "KS",
    "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
    "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS",
    "Missouri": "MO", "Montana": "MT", "Nebraska": "NE", "Nevada": "NV",
    "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM", "New York": "NY",
    "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH", "Oklahoma": "OK",
    "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN",
    "Texas": "TX", "Utah": "UT", "Vermont": "VT", "Virginia": "VA",
    "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY",
}

# --- Map visualization ---
#     map_qs = qs  # already filtered by state/age/date
    
#     map_counts = map_qs.exclude(apprehension_state='Unknown')\
#                     .exclude(apprehension_state__isnull=True)\
#                     .values('apprehension_state') \
#                     .annotate(count=Count('id')) \
#                     .order_by('-count')
#     map_counts = pd.DataFrame(list(map_counts))
#     map_counts = map_counts.sort_values('count', ascending=False).reset_index(drop=True)
#     map_counts['rank'] = map_counts.index + 1
#     map_counts['tier'] = (map_counts.index // 10) + 1
#     map_counts['tier'] = map_counts['tier'].clip(upper=5)

#     # map_counts['rank'] = map_counts['count'].rank(method='dense',ascending=False).astype(int)
#     # map_counts['tier'] = ((map_counts['rank']-1)//10)+1 # creating tier like tier 1, tier 2
#     # map_counts['tier'] = map_counts['tier'].clip(upper=5) # ensures any states above than rank 5 will have tier 5 color grading
#     map_counts['tier_str'] = map_counts['tier'].astype(str)
#     tier_colors = {
#     "1": "#08306B",  # very dark blue
#     "2": "#2171B5",  # dark blue
#     "3": "#4292C6",  # medium blue
#     "4": "#6BAED6",  # lighter blue
#     "5": "#C6DBEF"   # very light blue
# }
#     tier_labels = {
#     "1": "Top 1–10",
#     "2": "Rank 11–20",
#     "3": "Rank 21–30",
#     "4": "Rank 31–40",
#     "5": "Rank 41–50"
#     }

#     map_counts['tier_label'] = map_counts['tier_str'].map(tier_labels)

#     if not map_counts.empty:
#         map_counts = map_counts.rename(columns={'apprehension_state': 'state'})
#         map_counts['state'] = map_counts['state'].str.strip().str.title()
#         map_counts['state_code'] = map_counts['state'].map(state_abbrev)
#         map_counts = map_counts.dropna(subset=['state_code'])
#         map_counts['count'] = map_counts['count'].astype(int)

#         # Add hover text
#         map_counts['hover_text'] = map_counts['state'] + ': ' + map_counts['count'].astype(str)
#         def get_text_color(tier):
#             if tier in [1, 2]:  # dark tiers
#                 return "white"
#             else:  # light tiers
#                 return "black"
#         fig_map = px.choropleth(
#             map_counts,
#             locations='state_code',
#             locationmode="USA-states",
#             color='tier_str',
#             color_discrete_map=tier_colors,
#             scope="usa",
#             hover_name='state',
#             hover_data={'count': True, 'state_code': True,'tier_str':False},
#             title=f"Arrests by State ({selected_state})"
#         )

#         # Optional: add annotations (visible numbers on the map)
#         for i, row in map_counts.iterrows():
#             fig_map.add_scattergeo(
#                 locations=[row['state_code']],
#                 locationmode='USA-states',
#                 text=[f"{row['state_code']}<br>{row['count']}"],
#                 mode='text',
#                 hoverinfo='skip',
#                 showlegend=False,
#                 textfont=dict(size=12, color=get_text_color(row['tier']))
#             )

#         fig_map.update_layout( margin={"r":0,"t":50,"l":0,"b":0})
#         chart_map = fig_map.to_html(full_html=False, include_plotlyjs='cdn',
#                                     config={'displayModeBar':False})
#     else:
#         chart_map = "<p>No data to display on map</p>"
    # map_qs = qs  # already filtered by state/age/date

    # map_counts = map_qs.exclude(apprehension_state='nan')\
    #                 .exclude(apprehension_state__isnull=True)\
    #                 .values('apprehension_state') \
    #                 .annotate(count=Count('id')) \
    #                 .order_by('-count')
    # map_counts = pd.DataFrame(list(map_counts))
    # map_counts = map_counts.sort_values('count', ascending=False).reset_index(drop=True)
    # map_counts['rank'] = map_counts.index + 1
    # map_counts['tier'] = (map_counts.index // 10) + 1
    # map_counts['tier'] = map_counts['tier'].clip(upper=5)
    # map_counts['tier_str'] = map_counts['tier'].astype(str)
    # tier_colors = {
    #     "1": "#08306B",  # very dark blue
    #     "2": "#2171B5",  # dark blue
    #     "3": "#4292C6",  # medium blue
    #     "4": "#6BAED6",  # lighter blue
    #     "5": "#C6DBEF"   # very light blue
    # }

    # tier_labels = {
    #     "1": "Top 1–10",
    #     "2": "Rank 11–20",
    #     "3": "Rank 21–30",
    #     "4": "Rank 31–40",
    #     "5": "Rank 41–50"
    # }
    # map_counts['tier_label'] = map_counts['tier_str'].map(tier_labels)

    # if not map_counts.empty:
    #     map_counts = map_counts.rename(columns={'apprehension_state': 'state'})
    #     map_counts['state'] = map_counts['state'].str.strip().str.title()
    #     map_counts['state_code'] = map_counts['state'].map(state_abbrev)
    #     map_counts = map_counts.dropna(subset=['state_code'])
    #     map_counts['count'] = map_counts['count'].astype(int)

    #     # Add hover text
    #     map_counts['hover_text'] = map_counts['state'] + ': ' + map_counts['count'].astype(str)
    #     map_counts['count_formatted'] = map_counts['count'].apply(lambda x: f"{x:,}")
    #     def get_text_color(tier):
    #         if tier in [1, 2]:  # dark tiers
    #             return "white"
    #         else:  # light tiers
    #             return "black"

    #     fig_map = px.choropleth(
    #         map_counts[map_counts['count'] > 0],
    #         locations='state_code',
    #         locationmode="USA-states",
    #         color='tier_label',  
    #         color_discrete_map={
    #             "Top 1–10": "#08306B",
    #             "Rank 11–20": "#2171B5",
    #             "Rank 21–30": "#4292C6",
    #             "Rank 31–40": "#6BAED6",
    #             "Rank 41–50": "#C6DBEF"
    #         },
    #         scope="usa",
    #         hover_name='state',
    #         hover_data={
    #             'state_code': True,
    #             'count_formatted': True,
    #             'tier_label':False# hide this temporary column
    #         },
    #         labels = {'tier_labels':'Rank','count_formatted':'Number of arrests'},
    #         title=f"Arrests by State ({selected_state})"
    #     )
    #     # Optional: add annotations (visible numbers on the map)
    #     for i, row in map_counts.iterrows():
    #         fig_map.add_scattergeo(
    #             locations=[row['state_code']],
    #             locationmode='USA-states',
    #             text=[f"{row['state_code']}<br>{row['count']:,}"],  # formatted with commas
    #             mode='text',
    #             hoverinfo='skip',
    #             showlegend=False,
    #             textfont=dict(size=12, color=get_text_color(row['tier']))
    #         )

    #     fig_map.update_layout(margin={"r":0,"t":50,"l":0,"b":0},
    #                           legend_title_text = "State Arrest Tiers")
        
    #     chart_map = fig_map.to_html(
    #         full_html=False,
    #         include_plotlyjs='cdn',
    #         config={'displayModeBar': False}
    #     )
    # else:
    #     chart_map = "<p>No data to display on map</p>"        
    map_qs = qs  # already filtered by state/age/date
    if not map_qs.exists():
        map_counts = pd.DataFrame()
    else:
        map_counts = map_qs.exclude(apprehension_state='nan')\
                        .exclude(apprehension_state__isnull=True)\
                        .values('apprehension_state') \
                        .annotate(count=Count('id')) \
                        .order_by('-count')

        map_counts = pd.DataFrame(list(map_counts))

    # --- SAFETY CHECK: handle empty DataFrame before any column access ---
    if map_counts.empty:
        chart_map = "<p>No data to display on map</p>"
    else:
        map_counts = map_counts.sort_values('count', ascending=False).reset_index(drop=True)
        map_counts['rank'] = map_counts.index + 1
        map_counts['tier'] = (map_counts.index // 10) + 1
        map_counts['tier'] = map_counts['tier'].clip(upper=5)
        map_counts['tier_str'] = map_counts['tier'].astype(str)

        tier_colors = {
            "1": "#08306B",  # very dark blue
            "2": "#2171B5",  # dark blue
            "3": "#4292C6",  # medium blue
            "4": "#6BAED6",  # lighter blue
            "5": "#C6DBEF"   # very light blue
        }

        tier_labels = {
            "1": "Top 1–10",
            "2": "Rank 11–20",
            "3": "Rank 21–30",
            "4": "Rank 31–40",
            "5": "Rank 41–50"
        }
        map_counts['tier_label'] = map_counts['tier_str'].map(tier_labels)

        map_counts = map_counts.rename(columns={'apprehension_state': 'state'})
        map_counts['state'] = map_counts['state'].str.strip().str.title()
        map_counts['state_code'] = map_counts['state'].map(state_abbrev)
        map_counts = map_counts.dropna(subset=['state_code'])
        map_counts['count'] = map_counts['count'].astype(int)

        # Add hover text
        map_counts['hover_text'] = map_counts['state'] + ': ' + map_counts['count'].astype(str)
        map_counts['count_formatted'] = map_counts['count'].apply(lambda x: f"{x:,}")

        def get_text_color(tier):
            if tier in [1, 2]:  # dark tiers
                return "white"
            return "black"

        fig_map = px.choropleth(
            map_counts[map_counts['count'] > 0],
            locations='state_code',
            locationmode="USA-states",
            color='tier_label',
            color_discrete_map={
                "Top 1–10": "#08306B",
                "Rank 11–20": "#2171B5",
                "Rank 21–30": "#4292C6",
                "Rank 31–40": "#6BAED6",
                "Rank 41–50": "#C6DBEF"
            },
            scope="usa",
            hover_name='state',
            hover_data={
                'state_code': True,
                'count_formatted': True,
                'tier_label': False
            },
            labels={'tier_labels': 'Rank', 'count_formatted': 'Number of arrests'},
            title=f"Arrests by State ({selected_state})"
        )

        for i, row in map_counts.iterrows():
            fig_map.add_scattergeo(
                locations=[row['state_code']],
                locationmode='USA-states',
                text=[f"{row['state_code']}<br>{row['count']:,}"],
                mode='text',
                hoverinfo='skip',
                showlegend=False,
                textfont=dict(size=12, color=get_text_color(row['tier']))
            )

        fig_map.update_layout(margin={"r": 0, "t": 50, "l": 0, "b": 0},
                            legend_title_text="State Arrest Tiers")

        chart_map = fig_map.to_html(
            full_html=False,
            include_plotlyjs='cdn',
            config={'displayModeBar': False}
        )


########################   Heatmap   ############################################
     
    # # --- Treemap for Apprehension AOR ---
    if not qs.exists():
        aor_total_df = pd.DataFrame()
    else:
        aor_total_qs = qs.exclude(apprehension_aor='nan')\
                        .values('apprehension_aor') \
                        .annotate(count=Count('id')) \
                        .order_by('-count')

        aor_total_df = pd.DataFrame(list(aor_total_qs))   
    
    if not aor_total_df.empty:
        aor_total_df.sort_values('count', ascending=False).reset_index(drop=True)
        aor_total_df['text_color'] = ["white" if i < 7 else "#222222" for i in range(len(aor_total_df))]
        total_all = aor_total_df['count'].sum()
        aor_total_df['percent'] = 100 * aor_total_df['count'] / total_all
        aor_total_df['count_formatted'] = aor_total_df['count'].apply(lambda x:f"{x:,}")
        def clean_aor(name):
            if pd.isna(name) or not str(name).strip():
                return "Unknown"
            name = str(name).strip()
            # Replace the long phrase with 'AOR'
            return name.replace("Area of Responsibility", "AOR")

        aor_total_df['short_name'] = aor_total_df['apprehension_aor'].apply(clean_aor)

        # Build treemap with a constant root + UNIQUE leaf key (full AOR) to avoid merging
        fig_aor = px.treemap(
        aor_total_df,
        path=[Constant("AOR"), 'apprehension_aor'],  # unique leaves
        values='count',
        color='count',
        color_continuous_scale="Blues",  
        title="Arrests by AOR",
        custom_data=['short_name', 'count_formatted','count', 'percent']  # for text/hover
    )


        # Show custom text inside each tile
        # fig_aor.update_traces(
        # texttemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} (%{customdata[2]:.1f}%)",
        # textinfo="text",
        # insidetextfont=dict(size=26, color=aor_total_df['text_color']),  
        # # marker=dict(line=dict(width=1, color="white")),
        # root_color="rgba(0,0,0,0)",
        # maxdepth=2
        # )
        fig_aor.update_traces(
        texttemplate="<b>%{customdata[0]}</b><br>%{customdata[1]} (%{customdata[3]:.1f}%)",  
        # use formatted count (customdata[2]) for display
        textinfo="text",
        insidetextfont=dict(size=26, color=aor_total_df['text_color']),
        marker=dict(line=dict(width=1, color="white")),
        root_color="rgba(0,0,0,0)",
        maxdepth=2,
        hovertemplate="<b>%{customdata[0]}</b><br>Number of Arrests: %{customdata[2]}<br>% of total: %{customdata[3]:.1f}%<extra></extra>"
    )

        # Clean hover (same info, no extra box)
        fig_aor.update_traces(
            hovertemplate=(
            "<b>%{customdata[0]}</b><br>" +
            "Number of Arrests: %{customdata[2]:,}<br>" +
            "% of total: %{customdata[3]:.1f}%<extra></extra>"
        )

        )
        aor_total_df['is_root'] = False  # all real leaves
        # We'll treat the invisible root separately in hover

        fig_aor.update_traces(
            hoverinfo='skip'
        )

        fig_aor.update_layout(
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(173, 216, 230, 0.2)',
            uniformtext_minsize=10,
            uniformtext_mode="hide"
        )

        chart_aor = fig_aor.to_html(
            full_html=False,
            include_plotlyjs='cdn',  # or False if another chart already includes Plotly
            config={'displayModeBar': False}
        )
    else:
        chart_aor = "<p>No data for AOR treemap</p>"


#########################################################################################
    # --- Prepare dropdowns ---
    states = ['All'] + list(ArrestRecord.objects.values_list('apprehension_state', flat=True)
                           .distinct().order_by('apprehension_state'))
    compositions = ['All', 'Gender', 'Criminality']  # Age Category removed
    # age_groups = ['All', 'Minors', 'Early Adult', 'Middle Adult', 'Older Adults']
    age_groups = ['All',"Minors(0-17 years)","Early Adult(18-35 years)","Middle Adult(36-64 years)","Older Adults(65+ years)"]
    nationality_groups = ['All'] + list(
        ArrestRecord.objects.values_list('citizenship_country', flat=True)
        .distinct().order_by('citizenship_country')
    )
    # --- Date range for timeline inputs ---
    date_range = ArrestRecord.objects.aggregate(
        min_date=Min('apprehension_date'),
        max_date=Max('apprehension_date')
    )

    return render(request, 'arrestdashboard/dashboard.html', {
        'total_arrests': total_arrests,
        'chart_bar_month': chart_bar_month,
        'chart_bar_state': chart_bar_state,
        'chart_line': chart_line,
        'chart_map': chart_map,
        'chart_aor':chart_aor,
        'states': states,
        'selected_state': selected_state,
        'compositions': compositions,
        'selected_composition': selected_composition,
        'age_groups': age_groups,
        'selected_age_group': selected_age_group,
        'nationality_groups': nationality_groups,
        'selected_nationality':selected_nationality,
        'from_date': from_date,
        'to_date': to_date,
        'min_date': date_range['min_date'],
        'max_date': date_range['max_date'],
        'grand_total_arrest' : Grand_Total_Arrests,
        'first_date':first_date,
        'last_date':last_date
    })



def documentation(request):
    return render(request, 'arrestdashboard/documentation.html')
