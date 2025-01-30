import streamlit as st
import folium
from networkx.classes import nodes
from streamlit import session_state
from streamlit_folium import st_folium
from streamlit_tree_select import tree_select
import pandas as pd
from folium import plugins
import numpy as np

datafile = 'reference_marks2.csv'
all_df = pd.read_csv(datafile)
@st.cache_data
def get_data():
    """
    read data from reference mark file with columns OLDID,VILLAGE,AREA,Type,LatGRS,LongGRS,Y_LO,X_LO,ORTHOH
    :return: dictionary of pandas data frame with keys RM, BM, 'BPP', 'BPS', 'BPT'
    """
    df = pd.read_csv(datafile)
    df = df.round({'LatGRS': 6, 'LongGRS': 6})
    df = df.round({'X_LO': 3, 'Y_LO': 3})

    rm_df = df[df['Type'] == 'RM']
    bm_df = df[df['Type'] == 'BM']
    rm_dict = {'RM': rm_df, 'BM': bm_df}
    trig_df = df[df['Type'] == 'TRIG']

    bpp_df, bps_df, bpt_df = '', '', ''
    for xx, trig in zip([bpp_df, bps_df, bpt_df], ['BPP', 'BPS', 'BPT']):
        xx = trig_df[trig_df['OLDID'].str.contains(trig)]

        rm_dict[trig] = xx

    return rm_dict



def create_marker(lat, longi,name,clr):

    marker = folium.Marker(
                location=[lat, longi],
                popup=f"{name}",
                tooltip=f"{name}",
                icon=folium.Icon(clr)
        )
    return marker

@st.cache_data
def base_map():
    m = folium.Map(location=[-23, 24], zoom_start=6, prefer_canvas=True,attr='Google Maps, Esri Satellite' )

    # Add custom basemaps to folium
    basemaps = {
        'Google Maps': folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Maps',
            overlay=True,
            control=True,
            show=False
        ),
        'Google Satellite': folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=True,
            control=True
        ),
        'Google Terrain': folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=p&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Terrain',
            overlay=True,
            control=True
        ),
        'Google Satellite Hybrid': folium.TileLayer(
            tiles='https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
            attr='Google',
            name='Google Satellite',
            overlay=True,
            control=True
        ),
        'Esri Satellite': folium.TileLayer(
            tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            attr='Esri',
            name='Esri Satellite',
            overlay=True,
            control=True,
            show=False
        )
    }

    basemaps['Google Maps'].add_to(m)
    #basemaps['Google Satellite'].add_to(m)
    basemaps['Esri Satellite'].add_to(m)
    folium.LayerControl(collapsed=False).add_to(m)

    return m


def create_layers():
    df_dict = get_data()

    #st.write(df_dict)
    callback = """\
    function (row) {
        var icon, marker;
        icon = L.icon({iconUrl: row[3], iconSize: [25, 41]});
        marker = L.marker(new L.LatLng(row[0], row[1]));
        marker.setIcon(icon);       
        marker.bindPopup(row[2]).openPopup();
        marker.bindTooltip(row[4]).openTooltip();
        return marker;
    };
    """
    my_icons = {
        'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-gold.png',
        'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-orange.png',
        'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-yellow.png',
        'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-violet.png',
        'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png',
    }

    my_icons= dict(zip(df_dict.keys(), my_icons))


    layer_dict ={}
    for key in df_dict.keys():
        df = df_dict[key]

        finlist = []
        icolist=[]
        poplist=[]
        for vill, name,E,N,h in zip(df['VILLAGE'], df['OLDID'],df['Y_LO'],df['X_LO'],df['ORTHOH']):
            # print(f'{vill} has {ctr}')
            if np.isnan(h): h = ''
            labelfinal = "<h4><b><i>"+name+"</i></b></h4><h4> E: "+str(E)+"<br> N: "+str(N)+"<br> h: "+str(h)+"</h4>"
            ico=my_icons[key]
            finlist.append(labelfinal)
            icolist.append(ico)
            poplist.append("<h4><b><i>"+name+"</i></b></h4>")

        location_list = list(zip(df.LatGRS, df.LongGRS, finlist,icolist,poplist))

        rm_cluster = folium.plugins.FastMarkerCluster(data=location_list,callback=callback)

        rm_group = folium.map.FeatureGroup(name='RM', overlay=True, control=True, show=True)

        rm_cluster.add_to(rm_group)

        layer_dict[key]=rm_group

    return layer_dict
@st.cache_data
def convert_df(df):
   return df.to_csv(index=False).encode('utf-8')

def main():

    # page settings
    st.set_page_config(layout="wide")



    if 'checked' not in st.session_state:
        st.session_state['checked']=[]

    if 'zoom' not in st.session_state:
        st.session_state['zoom'] = 6

    if 'selected_p' not in st.session_state:
        st.session_state['selected_p'] = []
    if 'last' not in st.session_state:
        st.session_state['last'] = []


    # sidebar
    with st.sidebar:
        st.title(':blue-background[Layers]')

        ctrl = [

            {'label':'Trigonometric stations',
             'value':'trigs',
             'children':[
                 {'label':'BPP', 'value':'BPP'},
                 {'label':'BPS','value':'BPS'},
                 {'label': 'BPT', 'value': 'BPT'}
             ]},
            {'label':'Reference Marks',
             'value':'RM',
             },
            {'label':'height','value':'BM'},
            {'label': 'CORS', 'value': 'cors','disabled':True},
            {'label': 'Cadastral areas', 'value': 'cad','disabled':True},
            {'label':'Boreholes',
             'value':'all',
             'disabled':True,
             'children':[
                 {'label':'Government','value':'BH'},
                 {'label': 'Private', 'value': 'ZH'}
             ]}
        ]

        return_select = tree_select(ctrl, check_model='leaf',checked=['BPP'],expand_on_click=True, show_expand_all=True,
                                    expanded=['trigs'])

        st.divider()

        st.write(':blue-background[Search]')
        st.text_input(label='Village')

    checked = return_select['checked']

    lyr=create_layers()
    m=base_map()

    fg_list=[]

    for item in checked:

        if item=='RM':
            fg_list.append(lyr['RM'])

        if item=='BM':
            fg_list.append(lyr['BM'])

        if item=='BPP':
            fg_list.append(lyr['BPP'])

        if item=='BPS':
            fg_list.append(lyr['BPS'])

        if item=='BPT':
            fg_list.append(lyr['BPT'])

    col1, col2 = st.columns([3, 1])

    with col1:
        '# :blue-background[:flag-bw: Control Database]'
        control = folium.LayerControl(collapsed=False)
        st_data=st_folium(m,
                          key = 'mymap',
                          feature_group_to_add=fg_list,
                          use_container_width=True,
                          width=1500, height=700,
                          #returned_objects=[]
                          #layer_control=control
        )

    #st.session_state['last'] = st_data["last_object_clicked_tooltip"]
    with (col2):

        "# Download Marks"
        "#### Click marks to to view coordinates"
        last=''
        if st.button('Clear', key='del'):

            st.session_state['selected_p'] = []
            st.session_state['last']=st_data["last_object_clicked_tooltip"]


        elif st_data["last_object_clicked_tooltip"]:
            if st_data['last_active_drawing']:
                if st_data['last_active_drawing']['geometry']['type']=='Point':
                    if st_data["last_clicked"]!=st_data["last_object_clicked"]:
                        if st.session_state['selected_p']:
                            if st.session_state['selected_p'][-1]!=st_data["last_object_clicked_tooltip"]:
                                st.session_state['selected_p'].append(st_data["last_object_clicked_tooltip"])

                        else:
                            if st.session_state['last']!= st_data["last_object_clicked_tooltip"]:
                                st.session_state['selected_p'].append(st_data["last_object_clicked_tooltip"])


        #select_list = [st_data["last_object_clicked_tooltip"]]
        # st.markdown(
        #     """
        #     <style>
        #     [data-testid="stElementToolbar"] {
        #         display: none;
        #     }
        #     </style>
        #     """,
        #     unsafe_allow_html=True
        # )

        #st.write(st.session_state)
        dwn_df=pd.DataFrame()
        st.session_state['dwn'] = []
        with st.container(height=500, border=False):

            #if st.session_state['last'] != st_data["last_object_clicked_tooltip"]:

            if st.session_state['selected_p']:
                dwn_df=all_df[all_df['OLDID'].isin(st.session_state['selected_p'])][['OLDID','Y_LO','X_LO','ORTHOH','lzon']].reset_index(drop=True)
                st.dataframe(dwn_df,
                     hide_index=True, key='dwn'
                         )
        # st_data["last_object_clicked_tooltip"]=[]

        #st.sidebar.write(st.session_state)
        col1,col2,col3 = st.columns(3)
        #col1.button('Test', disabled=True)
        #col3.button('Download', disabled=True)
        col3.download_button(
            label="Download",
            data=convert_df(dwn_df),
            file_name="file.csv",
            mime="text/csv",
            key='download-csv',
            #disabled=True,
            help='click to download'
        )

if __name__ == "__main__":
    main()

