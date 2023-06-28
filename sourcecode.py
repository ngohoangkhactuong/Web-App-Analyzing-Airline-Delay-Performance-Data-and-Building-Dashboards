
# import required librarie
import pandas as pd
import dash
import dash_html_components as html
import dash_core_components as dcc
import plotly.graph_objects as go
import plotly.express as px
from dash.dependencies import Input, Output, State
from jupyter_dash import JupyterDash
from dash import no_update
import requests
import tarfile
from os import path
# Tạo 1 ứng dụng web dashboard
app = dash.Dash(__name__)
# Tắt cảnh báo khi sử dụng callback trong ứng dụng.
app.config.suppress_callback_exceptions = True

# Extracting the dataset
fname = 'airline_2m.tar.gz'
url = 'https://dax-cdn.cdn.appdomain.cloud/dax-airline/1.0.1/' + fname
r = requests.get(url)
open(fname , 'wb').write(r.content)

# Extracting the dataset
tar = tarfile.open(fname)
tar.extractall()
tar.close()

# Verifying the file was extracted properly
data_path = "airline_2m.csv"
path.exists(data_path)

airline_data =  pd.read_csv(data_path, encoding = "ISO-8859-1")

# Tiền xử lí dữ liệu

# Tạo 1 dataframe mới bằng cách loại bỏ những cột không cần thiết để thuận tiện cho việc vẽ biểu đồ

col = ['Year', 'Month', 'DayofMonth', 'DayOfWeek', 'FlightDate', 'Reporting_Airline','Flights','AirTime',
       'CancellationCode','DivAirportLandings','OriginState','OriginStateName','DestState','DestStateName',
      'CarrierDelay','WeatherDelay','NASDelay','SecurityDelay','LateAircraftDelay']

airline_data = airline_data[col]

# Filter và group dữ liệu cho việc vẽ biểu đồ

#  Tạo một danh sách các năm từ năm 2005 đến năm 2020.
year_list = [i for i in range(2005, 2021,1)]

def compute_data_choice_1(df):
    # Tính tổng số chuyến bay theo từng loại mã hủy bỏ trong mỗi tháng.
    bar_data = df.groupby(['Month','CancellationCode'])['Flights'].sum().reset_index()
    # Tính thời gian trung bình của các chuyến bay theo từng hãng hàng không trong mỗi tháng.
    line_data = df.groupby(['Month','Reporting_Airline'])['AirTime'].mean().reset_index()
    # Lọc ra các chuyến bay đã phải hạ cánh tại sân bay khác vì một lý do nào đó.
    div_data = df[df['DivAirportLandings'] != 0.0]
    # Tính tổng số chuyến bay xuất phát từ mỗi bang của Mỹ.
    map_data = df.groupby(['OriginState','OriginStateName'])['Flights'].sum().reset_index()
    # Tính tổng số chuyến bay đến từng bang của Mỹ và theo từng hãng hàng không.
    tree_data = df.groupby(['DestState','DestStateName', 'Reporting_Airline'])['Flights'].sum().reset_index()
    return bar_data, line_data, div_data, map_data, tree_data

def compute_data_choice_2(df):
    # Tính thời gian trung bình chờ đợi vì lý do delay của từng hãng hàng không trong mỗi tháng.
    avg_car = df.groupby(['Month','Reporting_Airline'])['CarrierDelay'].mean().reset_index()
    avg_weather = df.groupby(['Month','Reporting_Airline'])['WeatherDelay'].mean().reset_index()
    avg_NAS = df.groupby(['Month','Reporting_Airline'])['NASDelay'].mean().reset_index()
    avg_sec = df.groupby(['Month','Reporting_Airline'])['SecurityDelay'].mean().reset_index()
    avg_late = df.groupby(['Month','Reporting_Airline'])['LateAircraftDelay'].mean().reset_index()
    return avg_car, avg_weather, avg_NAS, avg_sec, avg_late

# Xây dựng layout cho webapp

# Application layout
app.layout = html.Div(children=[ # title of dash board
                                 html.H1('US Domestic Airline Flights Performance',
                                 style={'textAlign': 'center', 'color': '#503D36','font-size':24}),  
                                 
                                 html.Div([
                                     html.Div([
                                         html.Div(
                                                  [
                                                  html.H2('Report Type:', style={'margin-right': '2em'}),       
                                                  ]
                                         ), 
                                         # Tạo một dropdown để người dùng chọn loại dữ liệu muốn xem.
                                         # OPT1 : Yearly Airline Performance Report
                                         # OPT2 : Yearly Airline Delay Report
                                         dcc.Dropdown(id='input-type',
                                                      options=[
                                                               {'label': 'Yearly Airline Performance Report', 'value': 'OPT1'},
                                                               {'label': 'Yearly Airline Delay Report', 'value': 'OPT2'}
                                                              ],
                                                      #value='OPT1',
                                                      placeholder='Select a report type',
                                                      style={'width': '80%', 'padding': '3px', 'font-size': '20px', 'text-align-last': 'center'}
                                         )       
                                      ], style={'display':'flex'} # place them next to each other using the division style
                                     ),
                                     html.Div([
                                         html.Div([
                                             html.H2('Choose Year:', style={'margin-right': '2em'})
                                         ]),
                                         #  Tạo một dropdown để người dùng chọn năm muốn xem dữ liệu.
                                         dcc.Dropdown(id='input-year',
                                                      # update dropdown values using list comprehension
                                                      options=[{'label': i, 'value': i} for i in year_list],
                                                      #value='2010',
                                                      placeholder='Select a year',
                                                      style={'width': '80%', 'padding': '3px', 'font-size': '20px', 'text-align-last': 'center'}
                                         ),
                                      ], style={'display': 'flex'}
                                     ),  # place them next to each other using the division style
                                 ]),
                                 # Add computed graphs - add empty division and providing an id that will be updated during callback
                                 html.Div([ ],id='plot1'),
                                 html.Div([
                                     html.Div([ ], id='plot2'),
                                     html.Div([ ], id='plot3')
                                  ],style={'display': 'flex'} 
                                 ),
                                 html.Div([
                                     html.Div([ ], id='plot4'),
                                     html.Div([ ], id='plot5')
                                  ], style={'display': 'flex'}
                                 )
                     ])

#  Định nghĩa một hàm callback để cập nhật dữ liệu và đồ thị khi người dùng chọn lựa chọn của mình.
@app.callback([Output(component_id='plot1', component_property='children'),
               Output(component_id='plot2', component_property='children'),
               Output(component_id='plot3', component_property='children'),
               Output(component_id='plot4', component_property='children'),
               Output(component_id='plot5', component_property='children')
              ],
              [Input(component_id='input-type', component_property='value'),
               Input(component_id='input-year', component_property='value')
              ],
              [State('plot1', 'children'), State('plot2', 'children'),
               State('plot3', 'children'), State('plot4', 'children'),
               State('plot5', 'children')
              ] 
            )

# Định nghĩa function tính toán dữ liệu và return đồ thị.
def get_graph(chart, year, children1, children2, c3, c4, c5):
    # Select data
    df = airline_data[airline_data['Year']==int(year)]

    if chart=='OPT1':
        # Compute required information for creating graph from the data
        bar_data, line_data, div_data, map_data, tree_data = compute_data_choice_1(df)

        # Biểu đồ cột: số lượng chuyến bay bị hủy theo tháng.
        bar_fig = px.bar(bar_data, x='Month', y='Flights', color='CancellationCode', title='Monthly Flight Cancelation in '+ str(year))

        # Biểu đồ đường: thời gian bay trung bình của các chuyến bay theo tháng của từng hãng hàng không.
        line_fig = px.line(line_data, x='Month', y='AirTime', color='Reporting_Airline', title='Average monthly flight time (minutes) by airline in '+ str(year))

        # Biểu đồ tròn: phần trăm các chuyến bay chuyển hướng theo hãng hàng không.
        pie_fig = px.pie(div_data, values='Flights', names='Reporting_Airline', title='% of diverted flights by reporting airline in '+ str(year))

        # Bản đồ: số lượng chuyến bay từ mỗi tiểu bang sử dụng choropleth.
        map_fig = px.choropleth(map_data,
                                locations='OriginState',
                                color='Flights',
                                hover_data=['OriginState', 'Flights'],
                                locationmode='USA-states',  # Set to plot as US state
                                color_continuous_scale='GnBu',
                                hover_name='OriginStateName',
                                range_color=[0, map_data['Flights'].max()]
                                )
        map_fig.update_layout(
                              title_text= 'Number of flights from origin state in '+ str(year),
                              geo_scope= 'usa'
                              )  # plot only for USA instead of globe
        
        # Biểu đồ cây: số lượng chuyến bay đến mỗi tiểu bang từ mỗi hãng hàng không sử dụng treemap.
        tree_fig = px.treemap(tree_data, path=['DestState', 'Reporting_Airline'],
                              values='Flights',
                              color='Flights',
                              hover_name='DestStateName',
                              color_continuous_scale='RdBu',
                              title='Flight count by airline to destination state in '+ str(year)
                              )
        
        # Return dcc
        return [dcc.Graph(figure=tree_fig),
                dcc.Graph(figure=pie_fig),
                dcc.Graph(figure=map_fig),
                dcc.Graph(figure=bar_fig),
                dcc.Graph(figure=line_fig)
               ]
    else:
        # Compute required information for creating graph from the data
        avg_car, avg_weather, avg_NAS, avg_sec, avg_late = compute_data_choice_2(df)    

        # Create graph
        carrier_fig = px.line(avg_car, x='Month', y='CarrierDelay', color='Reporting_Airline', 
                              title='Average carrrier delay time (minutes) by airline in '+ str(year))
        weather_fig = px.line(avg_weather, x='Month', y='WeatherDelay', color='Reporting_Airline', 
                              title='Average weather delay time (minutes) by airline in '+ str(year))
        nas_fig = px.line(avg_NAS, x='Month', y='NASDelay', color='Reporting_Airline', 
                              title='Average NAS delay time (minutes) by airline  in '+ str(year))
        sec_fig = px.line(avg_sec, x='Month', y='SecurityDelay', color='Reporting_Airline', 
                              title='Average security delay time (minutes) by airline  in '+ str(year))
        late_fig = px.line(avg_late, x='Month', y='LateAircraftDelay', color='Reporting_Airline', 
                              title='Average late aircraft delay time (minutes) by airline  in '+ str(year))
        
        return [dcc.Graph(figure=carrier_fig), 
                dcc.Graph(figure=weather_fig), 
                dcc.Graph(figure=nas_fig), 
                dcc.Graph(figure=sec_fig), 
                dcc.Graph(figure=late_fig)
               ]    

# Run the app
if __name__=='__main__':
    # Đối số debug=False sẽ tắt chế độ gỡ lỗi, dev_tools_ui=False và dev_tools_props_check=False sẽ tắt các công cụ phát triển được tích hợp trong Dash.
    app.run_server(debug=False,dev_tools_ui=False,dev_tools_props_check=False)




