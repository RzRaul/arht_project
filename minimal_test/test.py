import datetime
import pandas as pd
import numpy as np
import json
import plotly
import plotly.express as px
import plotly.graph_objects as go

df = pd.read_csv("data.csv")
df['sens_time'] = pd.to_datetime(df['sens_time'])
# print(df.describe())
print(df.head())
df['sens_time'] = df['sens_time'].dt.strftime('%Y-%m-%d %H:%M')
df = df.replace(0, np.nan)

fig_temp17 = px.line(df, x='sens_time', y='temp_pin17', color='room_name')
fig_temp19 = px.line(df, x='sens_time', y='temp_pin19', color='room_name')
fig_temp23 = px.line(df, x='sens_time', y='temp_pin23', color='room_name')
fig_temp32 = px.line(df, x='sens_time', y='temp_pin32', color='room_name')
fig_temp33 = px.line(df, x='sens_time', y='temp_pin33', color='room_name')
fig_hum17 = px.line(df, x='sens_time', y='humidity_pin17', color='room_name')
fig_hum19 = px.line(df, x='sens_time', y='humidity_pin19', color='room_name')
fig_hum23 = px.line(df, x='sens_time', y='humidity_pin23', color='room_name')
fig_hum32 = px.line(df, x='sens_time', y='humidity_pin32', color='room_name')
fig_hum33 = px.line(df, x='sens_time', y='humidity_pin33', color='room_name')
temps = fig_temp17.data + fig_temp19.data + fig_temp23.data + fig_temp32.data + fig_temp33.data
hums =  fig_hum17.data + fig_hum19.data + fig_hum23.data +  fig_hum32.data + fig_hum33.data
# fig6 = go.Figure(data=fig3.data+fig4.data+fig5.data)
fig_comb= go.Figure(data=temps)
fig_comb.show()
# fig_temp17.show()
# fig_temp19.show()
# fig_temp23.show()
# fig_temp32.show()
# fig_temp33.show()
