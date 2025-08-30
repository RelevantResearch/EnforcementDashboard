from django.shortcuts import render
from django.db.models import Count
from django.db.models.functions import TruncMonth
from .models import ArrestRecord
import pandas as pd
import plotly.express as px

def dashboard(request):
    selected_state = request.GET.get('state', 'All')
    selected_composition = request.GET.get('composition', 'All')
    qs = ArrestRecord.objects.all()
    if selected_state != 'All':
        qs = qs.filter(apprehension_state__iexact=selected_state)

    total_arrests = qs.count()
    state_counts_qs = qs.values('apprehension_state') \
                        .annotate(count=Count('id')) \
                        .order_by('-count')
    state_counts = pd.DataFrame(list(state_counts_qs))
    state_counts = state_counts.rename(columns={'apprehension_state': 'state'})

    fig_bar_state = px.bar(state_counts, x='state', y='count', color='state', title='Arrests by State')
    fig_bar_state.update_layout(xaxis_title='State', yaxis_title='Number of Arrests')
    chart_bar_state = fig_bar_state.to_html(full_html=False, include_plotlyjs='cdn',config={'displayModeBar': False})
    monthly_counts_qs = qs.annotate(month=TruncMonth('apprehension_date')) \
                          .values('month') \
                          .annotate(count=Count('id')) \
                          .order_by('month')
    monthly_counts = pd.DataFrame(list(monthly_counts_qs))
    if not monthly_counts.empty:
        monthly_counts['month'] = pd.to_datetime(monthly_counts['month'])
    else:
        monthly_counts = pd.DataFrame(columns=['month', 'count'])
    if selected_composition == "Gender":
        gender_counts_qs = qs.values('gender') \
                             .annotate(month=TruncMonth('apprehension_date')) \
                             .annotate(count=Count('id')) \
                             .order_by('month')
        monthly_gender = pd.DataFrame(list(gender_counts_qs))
        if not monthly_gender.empty:
            monthly_gender['month'] = pd.to_datetime(monthly_gender['month'])
            fig_line = px.line(monthly_gender, x='month', y='count', color='gender', markers=True,
                               title=f"Monthly Arrests by Gender ({selected_state})")
            fig_bar_month = px.bar(monthly_gender, x='month', y='count', color='gender',
                                   title=f"Monthly Arrests by Gender ({selected_state})")
        else:
            fig_line = px.line(monthly_counts, x='month', y='count', markers=True,
                               title=f"Monthly Arrests Over Time ({selected_state})")
            fig_bar_month = px.bar(monthly_counts, x='month', y='count', text='count',
                                   title=f"Monthly Arrests Bar Chart ({selected_state})")

    elif selected_composition == "Criminality":
        criminality_counts_qs = qs.values('apprehension_criminality') \
                                  .annotate(month=TruncMonth('apprehension_date')) \
                                  .annotate(count=Count('id')) \
                                  .order_by('month')
        monthly_criminality = pd.DataFrame(list(criminality_counts_qs))
        if not monthly_criminality.empty:
            monthly_criminality['month'] = pd.to_datetime(monthly_criminality['month'])
            fig_line = px.line(monthly_criminality, x='month', y='count', color='apprehension_criminality', markers=True,
                               title=f"Monthly Arrests by Criminality ({selected_state})")
            fig_bar_month = px.bar(monthly_criminality, x='month', y='count', color='apprehension_criminality',
                                   title=f"Monthly Arrests by Criminality ({selected_state})")
        else:
            fig_line = px.line(monthly_counts, x='month', y='count', markers=True,
                               title=f"Monthly Arrests Over Time ({selected_state})")
            fig_bar_month = px.bar(monthly_counts, x='month', y='count', text='count',
                                   title=f"Monthly Arrests Bar Chart ({selected_state})")
    else:
        fig_line = px.line(monthly_counts, x='month', y='count', markers=True,
                           title=f"Monthly Arrests Over Time ({selected_state})")
        fig_bar_month = px.bar(monthly_counts, x='month', y='count', text='count',
                               title=f"Monthly Arrests Bar Chart ({selected_state})")
    chart_line = fig_line.to_html(full_html=False, include_plotlyjs=False,config={'displayModeBar': False})
    chart_bar_month = fig_bar_month.to_html(full_html=False, include_plotlyjs=False,config={'displayModeBar': False})
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
        "Unknown": None
    }

    map_qs = ArrestRecord.objects.all()
    if selected_state != 'All':
        map_qs = map_qs.filter(apprehension_state__iexact=selected_state)

    map_counts = map_qs.values('apprehension_state') \
                       .annotate(count=Count('id')) \
                       .order_by('-count')
    map_counts = pd.DataFrame(list(map_counts))
    map_counts = map_counts.rename(columns={'apprehension_state': 'state'})
    map_counts['state'] = map_counts['state'].str.strip().str.title()
    map_counts['state_code'] = map_counts['state'].map(state_abbrev)
    map_counts = map_counts.dropna(subset=['state_code'])
    map_counts['count'] = map_counts['count'].astype(int)

    if map_counts.empty:
        chart_map = "<p>No data to display on map</p>"
    else:
        fig_map = px.choropleth(
            map_counts,
            locations='state_code',
            locationmode="USA-states",
            color='count',
            color_continuous_scale="Blues",
            scope="usa",
            title=f"Arrests by State ({selected_state})"
        )
        fig_map.update_layout(
            height=600,  
            margin={"r":0,"t":50,"l":0,"b":0}  
        )
        chart_map = fig_map.to_html(full_html=False, include_plotlyjs=False, config={'displayModeBar':False})
    states = ['All'] + list(ArrestRecord.objects.values_list('apprehension_state', flat=True).distinct().order_by('apprehension_state'))
    compositions = ['All', 'Gender', 'Criminality']

    return render(request, 'arrestdashboard/dashboard.html', {
        'total_arrests': total_arrests,
        'chart_bar_state': chart_bar_state,
        'chart_line': chart_line,
        'chart_bar_month': chart_bar_month,
        'chart_map': chart_map,
        'states': states,
        'selected_state': selected_state,
        'compositions': compositions,
        'selected_composition': selected_composition,
    })
