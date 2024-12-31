import requests
import os
import socket

import streamlit as st

import pandas as pd

from pandas.api.types import (
    is_categorical_dtype,
    is_datetime64_any_dtype,
    is_numeric_dtype,
    is_object_dtype,
)

from datetime import datetime, timedelta

import matplotlib.pyplot as plt



# =============================================================================
# 
# General supporting functions
# 
# =============================================================================

# function to convert Excel-time to normal time
def excel_float_to_datetime(excel_float):
    return (datetime(1899, 12, 30) + timedelta(days=excel_float)).date()



# function to generate a filtering-enable dataframe
def filter_dataframe(df : pd.DataFrame, checkbox_name : str) -> pd.DataFrame:
    """
    Reference: https://blog.streamlit.io/auto-generate-a-dataframe-filtering-ui-in-streamlit-with-filter_dataframe/
    """
    modify = st.checkbox(checkbox_name)

    if not modify:
        return df

    df = df.copy()

    # Try to convert datetimes into a standard format (datetime, no timezone)
    for col in df.columns:
        if is_object_dtype(df[col]):
            try:
                df[col] = pd.to_datetime(df[col])
            except Exception:
                pass

        if is_datetime64_any_dtype(df[col]):
            df[col] = df[col].dt.tz_localize(None)

    modification_container = st.container()

    with modification_container:
        to_filter_columns = st.multiselect("Filter dataframe on", df.columns)
        for column in to_filter_columns:
            left, right = st.columns((1, 20))
            
            if is_categorical_dtype(df[column]) or df[column].nunique() < 30:
                user_cat_input = right.multiselect(
                    f"Values for {column}",
                    df[column].unique(),
                    default=list(df[column].unique()),
                )
                df = df[df[column].isin(user_cat_input)]
                
            elif is_numeric_dtype(df[column]):
                _min = float(df[column].min())
                _max = float(df[column].max())
                step = (_max - _min) / 100
                user_num_input = right.slider(
                    f"Values for {column}",
                    min_value=_min,
                    max_value=_max,
                    value=(_min, _max),
                    step=step,
                )
                df = df[df[column].between(*user_num_input)]
                
            elif is_datetime64_any_dtype(df[column]):
                user_date_input = right.date_input(
                    f"Values for {column}",
                    value=(
                        df[column].min(),
                        df[column].max(),
                    ),
                )
                if len(user_date_input) == 2:
                    user_date_input = tuple(map(pd.to_datetime, user_date_input))
                    start_date, end_date = user_date_input
                    df = df.loc[df[column].between(start_date, end_date)]
                    
            else:
                user_text_input = right.text_input(
                    f"Substring or regex in {column}",
                )
                if user_text_input:
                    df = df[df[column].astype(str).str.contains(user_text_input)]
             
    # # Format all float data
    # float_columns = df.select_dtypes(include=['float64', 'float']).columns
    # format_dict = {col: '{:.2f}' for col in float_columns}
    # df = df.style.format(format_dict)
    
    return df



# function to get file URLs from a GitHub repository
def get_github_file_url(repo_owner, repo_name, branch, file_name):
    api_url = f'https://api.github.com/repos/{repo_owner}/{repo_name}/git/trees/{branch}?recursive=1'
    response = requests.get(api_url)
    if response.status_code == 200:
        tree = response.json().get('tree', [])
        file_urls = [f'https://raw.githubusercontent.com/{repo_owner}/{repo_name}/{branch}/{file["path"]}' for file in tree if file['type'] == 'blob']
        
        # return file_urls
        for url in file_urls:
            if file_name in url:
                return url
            
        print('Cannot find the url for ', file_name, '.')
        return []
        
    else:
        print('Failed to fetch files from GitHub.')
        return []

# =============================================================================
# repo_owner = 'chitn'
# repo_name = 'trial'
# branch = 'main'
# file_name = 'pcb012a_2450_VN.xlsb'
# 
# file_url = get_github_file_url(repo_owner, repo_name, branch, file_name)
# print(file_url)
# =============================================================================
      


# function to check if Streamlit app is running locally or online, 
# by using os and socket libraries to determine the environment
# If the IP address of the machine running the app starts with 
# 127. or 192.168., it is likely running locally. 
# Otherwise, it is running online.
def is_running_locally():
    hostname = socket.gethostname()
    local_ip = socket.gethostbyname(hostname)
    st.write(hostname, ' ', local_ip)
    return local_ip.startswith('127.') or local_ip.startswith('192.168.')


# =============================================================================
# 
# Processing data from pcb012
# 
# =============================================================================

class xlsb_file:
    
    def __init__(self, xlsb_file_name, entity, rate):        
        self.data = pd.DataFrame()
        self.dict_mp = {}        
        self.stat = {}
        
        self.input(xlsb_file_name, entity, rate)
        
        self.df_2_dict()
        self.statistic()
        
        # self.to_excel("pcb012_VN")
        
                      
        
    def input(self, file_name : str, entity : str, rate : float):
        
        # =====================================================================
        # This function reads the xlsb file and does some cleaning works
        # =====================================================================

        if is_running_locally():
            # Read xlsb file - locally
            st.write('Running local.') 
        else:
            # Read xlsb file - github
            repo_owner = 'chitn'
            repo_name = 'trial'
            branch = 'main'            
            file_name = get_github_file_url(repo_owner, repo_name, branch, file_name)
            st.write('Running online.') 
            
        df = pd.read_excel(file_name, engine = 'pyxlsb', sheet_name = 'Report')
            
                
        # Set name for columns
        df.columns = ["Type",                  # 0
                      "WO",                    # 1
                      "2",                     # 2 WO_Linked
                      "3",                     # 3 Valuation_type
                      "4",                     # 4
                      "PM_MP",                 # 5
                      "Description",           # 6
                      "Project_type",          # 7
                      "8",                     # 8 Won/Lost
                      "9",                     # 9
                      "10",                    # 10 ACPE_status
                      "Project_tier",          # 11
                      "12",                    # 12 Invoice_type
                      "13",                    # 13
                      "14",                    # 14
                      "Contract_2d_invoiced",  # 15
                      "16",                    # 16
                      "17",                    # 17
                      "18",                    # 18
                      "19",                    # 19
                      "20",                    # 20
                      "21",                    # 21
                      "Contract_2d_total",     # 22
                      "Contract_budget",       # 23
                      "Cost_2d_total",         # 24
                      "Cost_2d_txt",           # 25
                      "Cost_2d_subcon",        # 26
                      "Cost_2d_others",        # 27
                      "Cost_budget_total",     # 28
                      "Cost_budget_txt",       # 29
                      "Cost_budget_subcon",    # 30
                      "Cost_budget_contin",    # 31
                      "Cost_budget_others",    # 32
                      "Cost_4cast_total",      # 33
                      "Cost_4cast_txt",        # 34
                      "Cost_4cast_subcon",     # 35
                      "Cost_4cast_contin",     # 36
                      "Cost_4cast_others",     # 37
                      "Date_budget",           # 38
                      "Date_4cast",            # 39
                      "Ratio_invoiced %",      # 40
                      "Ratio_spent %",         # 41
                      "Ratio_txt %",           # 42
                      "43",                    # 43
                      "PR_month",              # 44
                      "PR_year",               # 45
                      "PR_2date",              # 46
                      "PR_budgeted_selling",   # 47
                      "PR_4casted",            # 48
                      "PR_4casted_execution",  # 49
                      "PR_net_year",           # 50
                      "PR_net_2date",          # 51
                      "52",                    # 52
                      "53",                    # 53
                      "54",                    # 54
                      "55",                    # 55
                      "56",                    # 56
                      "57",                    # 57
                      "58",                    # 58
                      "4cast_change_pr",       # 59
                      "4cast_change_contin",   # 60
                      "61",                    # 61
                      "62",                    # 62
                      "63",                    # 63
                      "64",                    # 64
                      "65",                    # 65
                      "66",                    # 66
                      "67",                    # 67
                      "Outstanding_inv",       # 68
                      "69",                    # 69
                      "70",                    # 70
                      "Inv_oldest_unpaid",     # 71
                      "Inv_most_recent",       # 72
                      "Inv_base",              # 73
                      "WIP_gross",             # 74
                      "Inv_cost",              # 75
                      "WIP_net",               # 76
                      "77",                    # 77
                      "78",                    # 78
                      "79",                    # 79
                      "80",                    # 80
                      "81",                    # 81
                      "82",                    # 82
                      "Workload_firm",         # 83
                      "WO_date_start",         # 84
                      "WO_date_end",           # 85
                      "86",                    # 86 Outstanding_com
                      "Customer",              # 87
                      "88",                    # 88
                      "89",                    # 89 Department
                      "90",                    # 90
                      "91",                    # 91 PM_project
                      "92",                    # 92 PM_workoder
                      "93",                    # 93 ADAG
                      "94",                    # 94 Project_admin
                      "95",                    # 95 Project_controller
                      "96",                    # 96
                      "97",                    # 97
                      "98",                    # 98
                      "99"                     # 99
                      ]
        
        
        # Delete the first 17 rows of trivial info
        df = df.iloc[17:]
        df.reset_index(drop=True, inplace=True)
        
        
        # Delete all blank rows
        df = df[df["Type"] != "MPZ"]
           
                
        # Delete all columns with name as a number
        columns = [x for x in df.columns if not x.isdigit()]
        df = df[columns]
        
        
        # Change format of columns to float & currency
        columns = [x for x in df.columns if x.startswith('Contract') or 
                                            x.startswith('Cost') or 
                                            x.startswith('PR') or 
                                            x.startswith('4cast') or 
                                            x.startswith('Outstanding_inv') or 
                                            x.startswith('Inv_base') or
                                            x.startswith('Inv_cost') or 
                                            x.startswith('WIP') or 
                                            x.startswith('Workload_firm') ]
        df[columns] = df[columns].astype(float)
        df[columns] = df[columns] * rate
        
        
        # Change format of columns to float
        columns = [x for x in df.columns if x.startswith('Ratio')]
        df[columns] = df[columns].astype(float)
        df[columns] = df[columns]
        
        
        # Change format of columns to Date
        columns = [x for x in df.columns if ('Date' in x) or
                                            ('WO_date' in x) or
                                            ('Inv_oldest' in x) or
                                            ('Inv_most' in x) ]
        for col in columns:
            df[col] = df[col].fillna(1)
            df[col] = df[col].apply(excel_float_to_datetime)
            
            
        # Add a column to identify Entity
        df["Entity"] = entity
            
        
        # Change format of columns to Category
        columns = ["Type", "WO", "PM_MP", "Project_type", "Project_tier", "Entity"]
        df[columns] = df[columns].astype("category")
        
        
        # Store df to data
        self.data = df



    def to_excel(self, excel_file_name : str): 
        
        # =====================================================================
        # This function prints the whole dataframe into an Excel file
        # =====================================================================
        
        # Create a Pandas Excel writer using xlsxwriter as the engine
        writer = pd.ExcelWriter(excel_file_name + ".xlsx", engine="xlsxwriter")
        
        # Convert the dataframe to an xlsxwriter Excel object
        self.data.to_excel(writer, sheet_name=self.name, index=False)
        
        workbook  = writer.book
        worksheet = writer.sheets[self.name]
        
        # Filter numeric columns to be formatted
        columns = [x for x in self.data.columns if x.startswith('Contract') or 
                                                   x.startswith('Cost') or  
                                                   x.startswith('PR') or 
                                                   x.startswith('4cast') or 
                                                   x.startswith('Outstanding_inv') or 
                                                   x.startswith('Inv_base') or
                                                   x.startswith('Inv_cost') or 
                                                   x.startswith('WIP') or 
                                                   x.startswith('Workload_firm') ]
        
        # Define a format for comma style
        comma_format = workbook.add_format({'num_format': '#,##0'})
        comma_format = workbook.add_format({'num_format': 44})
        
        # Apply the comma format to the numeric columns
        for col in columns:
            col_idx = self.data.columns.get_loc(col)  # get_loc returns zero-based index, add 1 for Excel column index
            worksheet.set_column(col_idx, col_idx, None, comma_format)
           
        # Save the Excel file
        writer.close()
        
        
        
    def df_2_dict(self):
        
        # =====================================================================
        # This function converts a dataframe to a nested dictionary of
        # Master projects, Projects, Workorders
        # =====================================================================
        
        # Convert each row into a dictionary
        row_dicts = {}
        for index, row in self.data.iterrows():
            row_dicts[row['WO']] = row.to_dict()
            
        # Remove the 'WO' key from each dictionary
        for key in row_dicts:
            del row_dicts[key]['WO']
            
        # Seperate dictionaries of MPs, PRs and WOs
        dict_pr = {}
        dict_wo = {}
        
        
        for key, value in row_dicts.items():
            new_dict = {'main' : value}
            if len(key) == 6:
                self.dict_mp[key] = new_dict
            elif len(key) == 10:
                dict_pr[key] = new_dict
            elif len(key) == 14:
                dict_wo[key] = new_dict
              
                
        for key, value in dict_wo.items():
            for item in dict_pr:
                if (item in key):
                    dict_pr[item][key] = value
                    break 
                  
                    
        for key, value in dict_pr.items():
            for item in self.dict_mp:
                if (item in key):
                    self.dict_mp[item][key] = value
                    break                           



    def statistic(self, *args):
        
        # =====================================================================
        # This function does a statistic for an entity
        # =====================================================================
        
        unique_mp = self.data['WO'].apply(lambda x: x if len(x) == 6  else None).unique() 
        unique_pr = self.data['WO'].apply(lambda x: x if len(x) == 10 else None).unique() 
        unique_wo = self.data['WO'].apply(lambda x: x if len(x) == 14 else None).unique() 
        unique_pm = self.data['PM_MP'].unique()     
                
        self.stat['mp_list'] = unique_mp.tolist()
        self.stat['mp_no'] = len(self.stat['mp_list'])
        
        self.stat['pr_list'] = unique_pr.tolist()
        self.stat['pr_no'] = len(self.stat['pr_list'])
        
        self.stat['wo_list'] = unique_wo.tolist()
        self.stat['wo_no'] = len(self.stat['wo_list'])
        
        self.stat['pm_list'] = unique_pm.tolist()
        self.stat['pm_no'] = len(self.stat['pm_list'])
        
        Contract_budget = self.data.loc[self.data['Type'] == 'MP', 'Contract_budget'].sum()
        Contract_2d_invoiced = self.data.loc[self.data['Type'] == 'MP', 'Contract_2d_invoiced'].sum()
        Contract_2d_total = self.data.loc[self.data['Type'] == 'MP', 'Contract_2d_total'].sum()
        Outstanding_inv = self.data.loc[self.data['Type'] == 'MP', 'Outstanding_inv'].sum()
        Workload_firm = self.data.loc[self.data['Type'] == 'MP', 'Workload_firm'].sum()
        
        self.stat['Contract_budget'] = Contract_budget
        self.stat['Contract_2d_invoiced'] = Contract_2d_invoiced
        self.stat['Contract_2d_total'] = Contract_2d_total
        self.stat['Outstanding_inv'] = Outstanding_inv
        self.stat['Workload_firm'] = Workload_firm
        
        for ar in args:
            if ar == 'Print':
                print('Contract budgetted  {:17,.0f}'.format(Contract_budget))
                print('Contract invoiced    {:17,.0f}'.format(Contract_2d_invoiced))
                print('Contract to date    {:17,.0f}'.format(Contract_2d_total))
                print('Outstanding invoice {:17,.0f}'.format(Outstanding_inv))
                print('Workload firm       {:17,.0f}'.format(Workload_firm))                    
     
        
 
# =============================================================================
# 
# Web-app
# 
# =============================================================================

class streaming:
    def __init__(self):
        self.source = pd.DataFrame()
                
        # Initialise a page
        st.set_page_config(layout="wide")
        st.title("Streamlit | Performance of Maritime Vietnam AG @ ctn")
                
        if 'source' not in st.session_state:
            st.session_state.source = pd.DataFrame()
    
        # self.input_single()
        self.input_form()
        
        self.source = st.session_state.source
        
        self.online()
            
    
    # =========================================================================
    # NEED A SERIOUS UPDATE ON SUBMIT_BUTTON FUNCTION TO OPERATE PROPERLY
    # =========================================================================
    def input_form_long(self):
        # Create a form
        with st.form(key='pcb012'):
            num_items = st.number_input('Number of entities', 
                                        min_value = 1, 
                                        max_value = 10, 
                                        value = 1)
            items = []
            for i in range(num_items):
                col1, col2, col3 = st.columns(3)
                with col1:
                    entity = st.selectbox(f'Entity {i+1}', 
                                          ['VN', 'NL', 'UK', 'SG', 'PH', 'ML'], 
                                          key=f'entity_{i+1}')
                with col2:
                    rate = st.number_input(f'Rate {i+1}', key = f'rate_{i+1}') 
                with col3:   
                    file_name = st.text_input(f'File name {i+1}', key = f'name_{i+1}')
                items.append({"Entity": entity, "Rate": rate, "File name": file_name})
                
            submit_button = st.form_submit_button(label = "Submit")
            
            
        if submit_button:
            tmp = pd.DataFrame()
            
            # Create a DataFrame from the input data
            df = pd.DataFrame(items)            
            for index, row in df.iterrows():
                new = xlsb_file(row["File name"]+".xlsb", row["Entity"])
                tmp = pd.concat([tmp, new.data], 
                                 ignore_index = True, 
                                 sort = False)            
            self.source = tmp
            
            self.switch_on = True
    # =========================================================================
    # NEED A SERIOUS UPDATE ON SUBMIT_BUTTON FUNCTION TO OPERATE PROPERLY
    # =========================================================================
            
            
            
    def input_form(self):
        # Create a form
        with st.form(key='pcb012'):
            suffices = ['VN', 'NL', 'UK', 'SG', 'PH', 'ML']
            rates = [0] * 6
            cola, colb, col1, col2, col3, col4, col5, col6 = st.columns(8) 
            with cola:
                base_name = st.selectbox('Base pcb012 name', 
                                         ['pcb012a_2450'],
                                         key='name', index=0)
            with colb:
                xrate = st.number_input('Shown in EUR|Rate:', 
                                        key='base', value=26600)                
            with col1:
                rates[0] = st.number_input('VN|VND 1.00', key='rate_vn', value=1)
            with col2:
                rates[1] = st.number_input('NL|EUR->VND: 26,600', key='rate_nl', value=26600)
            with col3:
                rates[2] = st.number_input('UK|GBP->VND: 32,000', key='rate_uk', value=32000)
            with col4:
                rates[3] = st.number_input('SG|SGD->VND: 18,750', key='rate_sg', value=18750)
            with col5:
                rates[4] = st.number_input('PH|PHP->VND: 440', key='rate_ph', value=440)
            with col6:
                rates[5] = st.number_input('ML|MYR->VND: 5,700', key='rate_ml', value=5700) 
                
            submit_button = st.form_submit_button(label = "Submit")
            
            
        if submit_button:    
            tmp = pd.DataFrame()
            
            # Create a DataFrame from the input data
            for rate, suffix in zip(rates, suffices):
                if rate != 0:
                    name = base_name + "_" + suffix + ".xlsb"  
                    try:
                        # st.write(get_github_file_url('chitn', 'trial', 'main', name))                        
                        new = xlsb_file(name, suffix, rate / xrate)
                        tmp = pd.concat([tmp, new.data], 
                                        ignore_index = True, 
                                        sort = False)  
                    except:
                        st.write(name + " does not exit, cannot be accessed or contains no data.")
            
            st.session_state.source = tmp
                        
            self.source = st.session_state.source
            
            
            
    def input_single(self):
        pcb012_vn = xlsb_file("pcb012a_2451 VN.xlsb", "VN", 1)
        pcb012_nl = xlsb_file("pcb012a_2451 NL.xlsb", "NL", 26600)
        
        tmp = pd.concat([pcb012_vn.data, pcb012_nl.data],
                        ignore_index = True, 
                        sort = False)
        
        st.session_state.source = tmp
                    
        self.source = st.session_state.source
        
        

    def online(self):            
        # Define tabs for pcb012
        tab_info, tab_cnc, tab_pr, tab_wo, tab_result = st.tabs(["012 | Info",
                                                                 "012 | Contract & Cost",
                                                                 "012 | Contract & Cost - PR",
                                                                 "012 | Contract & Cost - WO",
                                                                 "012 | Project results"])
                
        incline = 75
        top = 20
        
        with tab_info:
            data = st.session_state.source
            
            if data.shape[0] == 0:
                st.write('Need to load data first...')
            else:
                columns = ["Entity", "PM_MP", "Type", "WO", "Description", 
                           "Project_type", "Project_tier", "Customer", "WO_date_start", "WO_date_end", 
                           "Contract_budget", "Contract_2d_invoiced",
                           "Outstanding_inv", "Workload_firm"]
                
                filter_df = filter_dataframe(data[columns], "Filters for Info")
                st.dataframe(filter_df)
                
                st.header("Some statistics for Vietnam entity: to be updated")
            
            
        with tab_cnc:             
            data = st.session_state.source
            
            if data.shape[0] == 0:
                st.write('Need to load data first...')
            else:
                columns = ["PM_MP", "Entity", "WO", "Description", 
                           "Contract_2d_invoiced", "Contract_2d_total", "Contract_budget", 
                           "Cost_2d_total", "Cost_budget_total", "Cost_4cast_total", 
                           "WIP_gross", "WIP_net", 
                           "Outstanding_inv", "Inv_oldest_unpaid", "Inv_most_recent", "Inv_base", "Inv_cost", 
                           "Ratio_spent %", "Workload_firm", "Type"]
                
                filter_df = filter_dataframe(data[columns], "Filters for Contract & Cost")
                filter_df = filter_df[filter_df['Type'] == 'MP']
                st.dataframe(filter_df)
                
                st.header("Contract & Cost | Master projects")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Create a pie chart
                    conditions = (filter_df['Contract_budget'] > 0) & (filter_df['Type'] == 'MP')
                    df_plot = filter_df[conditions].nlargest(10,'Contract_budget').sort_values(by=['Contract_budget'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | Contract budget')
                    ax.pie(df_plot['Contract_budget'], labels=df_plot['WO'], autopct='%1.f%%', startangle=90)
                    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
                    
                    # Display the pie chart in Streamlit
                    st.pyplot(fig)
                    
                with col2:
                    # Create a bar chart
                    conditions = (filter_df['Contract_budget'] > 0) & (filter_df['Type'] == 'MP')
                    df_plot = filter_df[conditions].nlargest(top,'Ratio_spent %').sort_values(by=['Ratio_spent %'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | Invoiced / Budget')
                    ax.bar(df_plot['WO'], df_plot['Contract_2d_invoiced'] / df_plot['Contract_budget'] * 100, label=df_plot['WO'])
                    ax.set_ylim(0,120)
                    ax.grid(color='gray', linestyle='dashed')
                    plt.xticks(rotation=incline)
                    plt.ylabel('Percentage of invoiced')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col3:
                    # Create a bar chart
                    conditions = (filter_df['Contract_budget'] > 0) & (filter_df['Type'] == 'MP')
                    df_plot = filter_df[conditions].nlargest(top,'Workload_firm').sort_values(by=['Workload_firm'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | Workload firm')
                    ax.bar(df_plot['WO'], df_plot['Workload_firm'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    plt.xticks(rotation=incline)
                    plt.ylabel('Worload remaining [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col4:
                    # Create a bar chart
                    conditions = (filter_df['Contract_budget'] > 0) & (filter_df['Type'] == 'MP')
                    df_plot = filter_df[conditions].nlargest(top,'Outstanding_inv').sort_values(by=['Outstanding_inv'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | Outstanding invoices')
                    ax.bar(df_plot['WO'], df_plot['Outstanding_inv'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    plt.xticks(rotation=incline)
                    plt.ylabel('Amount [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
            
            
        with tab_pr:             
            data = st.session_state.source
            
            if data.shape[0] == 0:
                st.write('Need to load data first...')
            else:
                columns = ["PM_MP", "Entity", "WO", "Description",  
                           "Cost_2d_total", "Cost_2d_txt", "Cost_2d_subcon", "Cost_2d_others", 
                           "Cost_budget_total", "Cost_budget_txt", "Cost_budget_subcon", "Cost_budget_contin", "Cost_budget_others", 
                           "Cost_4cast_total", "Cost_4cast_txt", "Cost_4cast_subcon", "Cost_4cast_contin", "Cost_4cast_others", 
                           "4cast_change_pr", "4cast_change_contin", 
                           "Ratio_invoiced %", "Ratio_spent %", "Ratio_txt %",  
                           "Date_budget", "Date_4cast", "Type"]
                
                filter_df = filter_dataframe(data[columns], "Filters for Contract & Cost - PR")
                filter_df = filter_df[filter_df['Type'] == 'PR']
                st.dataframe(filter_df)
                
                st.header("Contract & Cost | Projects")
                
                col1, col2, col3, col4 = st.columns(4)  
                
                with col1:
                    # Create a bar chart
                    conditions = (filter_df['Cost_budget_total'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'Cost_budget_total').sort_values(by=['Cost_budget_total'])
                    fig, ax = plt.subplots()
                    ax.set_title('Projects | Cost budgetted')
                    ax.bar(df_plot['WO'], df_plot['Cost_budget_total'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10**2,2*10**6)
                    plt.xticks(rotation=incline)
                    plt.ylabel('Cost budgetted [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col2:
                    # Create a bar chart
                    conditions = (filter_df['Cost_2d_total'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'Cost_2d_total').sort_values(by=['Cost_2d_total'])
                    fig, ax = plt.subplots()
                    ax.set_title('Projects | Cost to-date')
                    ax.bar(df_plot['WO'], df_plot['Cost_2d_total'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10**2,2*10**6)
                    plt.xticks(rotation=incline)
                    plt.ylabel('Cost to-date [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col3:
                    # Create a bar chart
                    conditions = (filter_df['Cost_budget_contin'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'Cost_budget_contin').sort_values(by=['Cost_budget_contin'])
                    fig, ax = plt.subplots()
                    ax.set_title('Projects | Contingency')
                    ax.bar(df_plot['WO'], df_plot['Cost_budget_contin'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10**2,2*10**6)
                    plt.xticks(rotation=incline)
                    plt.ylabel('Contingency [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col4:
                    # Create a bar chart
                    conditions = (filter_df['Ratio_spent %'] > 0) & (filter_df['Ratio_spent %'] < 120)
                    df_plot = filter_df[conditions].nlargest(round(top*1.5),'Ratio_spent %').sort_values(by=['Ratio_spent %'])
                    fig, ax = plt.subplots()
                    ax.set_title('Projects | Ratio_spent %')
                    ax.bar(df_plot['WO'], df_plot['Ratio_spent %'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_ylim(0,120)
                    plt.xticks(rotation=90)
                    plt.ylabel('Budget spent [%]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
        
        
        with tab_wo:            
            data = st.session_state.source
            
            if data.shape[0] == 0:
                st.write('Need to load data first...')
            else:
                columns = ["PM_MP", "Entity", "WO", "Description",  
                           "Cost_2d_total", "Cost_2d_txt", "Cost_2d_subcon", "Cost_2d_others", 
                           "Cost_budget_total", "Cost_budget_txt", "Cost_budget_subcon", "Cost_budget_contin", "Cost_budget_others", 
                           "Cost_4cast_total", "Cost_4cast_txt", "Cost_4cast_subcon", "Cost_4cast_contin", "Cost_4cast_others", 
                           "4cast_change_contin", 
                           "Ratio_invoiced %", "Ratio_spent %", "Ratio_txt %",  
                           "Date_budget", "Date_4cast", "Type"]
                
                filter_df = filter_dataframe(data[columns], "Filters for Contract & Cost - WO")
                filter_df = filter_df[filter_df['Type'] == 'WO']
                st.dataframe(filter_df)
                
                st.header("Contract & Cost | Workorders")
                
                col1, col2, col3, col4 = st.columns(4)  
                
                with col1:
                    # Create a bar chart
                    conditions = (filter_df['Cost_budget_total'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'Cost_budget_total').sort_values(by=['Cost_budget_total'])
                    fig, ax = plt.subplots()
                    ax.set_title('Projects | Cost budgetted')
                    ax.bar(df_plot['WO'], df_plot['Cost_budget_total'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10**2,2*10**6)
                    plt.xticks(rotation=incline)
                    plt.ylabel('Cost budgetted [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col2:
                    # Create a bar chart
                    conditions = (filter_df['Cost_2d_total'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'Cost_2d_total').sort_values(by=['Cost_2d_total'])
                    fig, ax = plt.subplots()
                    ax.set_title('Projects | Cost to-date')
                    ax.bar(df_plot['WO'], df_plot['Cost_2d_total'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10**2,2*10**6)
                    plt.xticks(rotation=incline)
                    plt.ylabel('Cost to-date [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col3:
                    # Create a bar chart
                    conditions = (filter_df['Cost_budget_contin'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'Cost_budget_contin').sort_values(by=['Cost_budget_contin'])
                    fig, ax = plt.subplots()
                    ax.set_title('Projects | Contingency')
                    ax.bar(df_plot['WO'], df_plot['Cost_budget_contin'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10**2,2*10**6)
                    plt.xticks(rotation=incline)
                    plt.ylabel('Contingency [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col4:
                    # Create a bar chart
                    conditions = (filter_df['Ratio_spent %'] > 0) & (filter_df['Ratio_spent %'] < 120)
                    df_plot = filter_df[conditions].nlargest(round(top*1.5),'Ratio_spent %').sort_values(by=['Ratio_spent %'])
                    fig, ax = plt.subplots()
                    ax.set_title('Projects | Ratio_spent %')
                    ax.bar(df_plot['WO'], df_plot['Ratio_spent %'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_ylim(0,120)
                    plt.xticks(rotation=90)
                    plt.ylabel('Budget spent [%]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
            
            
            
        with tab_result:
            data = st.session_state.source
            
            if data.shape[0] == 0:
                st.write('Need to load data first...')
            else:
                columns = ["PM_MP", "Entity", "WO", "Description", 
                           "PR_month", "PR_year", "PR_2date", "PR_net_year", "PR_net_2date", 
                           "PR_budgeted_selling", 
                           "PR_4casted", "PR_4casted_execution", "4cast_change_pr", "Type"]
                
                filter_df = filter_dataframe(data[columns], "Filters for Project results")
                filter_df = filter_df[filter_df['Type'] == 'MP']
                st.dataframe(filter_df)
                
                st.header("Project results")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Create a bar chart
                    conditions = (filter_df['PR_month'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'PR_month').sort_values(by=['PR_month'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | POSITIVE Result this month')
                    ax.bar(df_plot['WO'], df_plot['PR_month'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10,5*10**5)
                    plt.xticks(rotation=incline)
                    plt.ylabel('POSITIVE Result this month [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col2:
                    # Create a bar chart
                    conditions = (filter_df['PR_net_2date'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'PR_net_2date').sort_values(by=['PR_net_2date'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | POSITIVE Result to-date')
                    ax.bar(df_plot['WO'], df_plot['PR_net_2date'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10,5*10**5)
                    plt.xticks(rotation=incline)
                    plt.ylabel('POSITIVE Result to-date [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col3:
                    # Create a bar chart
                    conditions = (filter_df['PR_4casted'] > 0)
                    df_plot = filter_df[conditions].nlargest(top,'PR_4casted').sort_values(by=['PR_4casted'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | POSITIVE Result forcasted')
                    ax.bar(df_plot['WO'], df_plot['PR_4casted'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10,5*10**5)
                    plt.xticks(rotation=incline)
                    plt.ylabel('POSITIVE Result forcasted [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col4:
                    # Create a pie chart
                    conditions = (filter_df['PR_4casted'] > 0)
                    df_plot = filter_df[conditions].nlargest(10,'PR_4casted').sort_values(by=['PR_4casted'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | POSITIVE Result forcasted')
                    ax.pie(df_plot['PR_4casted'], labels=df_plot['WO'], autopct='%1.f%%', startangle=90)
                    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
                    
                    # Display the pie chart in Streamlit
                    st.pyplot(fig)
                    
                    
                    
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    # Create a bar chart
                    conditions = (filter_df['PR_month'] < 0)
                    df_plot = filter_df[conditions].nsmallest(top,'PR_month').sort_values(by=['PR_month'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | NEGATIVE Result this month')
                    ax.bar(df_plot['WO'], -df_plot['PR_month'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10,5*10**5)
                    plt.xticks(rotation=incline)
                    plt.ylabel('NEGATIVE Result this month [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                                                      
                with col2:
                    # Create a bar chart
                    conditions = (filter_df['PR_net_2date'] < 0)
                    df_plot = filter_df[conditions].nsmallest(top,'PR_net_2date').sort_values(by=['PR_net_2date'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | NEGATIVE Result to-date')
                    ax.bar(df_plot['WO'], -df_plot['PR_net_2date'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10,5*10**5)
                    plt.xticks(rotation=incline)
                    plt.ylabel('NEGATIVE Result to-date [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                                                      
                with col3:
                    # Create a bar chart
                    conditions = (filter_df['PR_4casted'] < 0)
                    df_plot = filter_df[conditions].nsmallest(top,'PR_4casted').sort_values(by=['PR_4casted'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | NEGATIVE Result forcasted')
                    ax.bar(df_plot['WO'], -df_plot['PR_4casted'], label=df_plot['WO'])
                    ax.grid(color='gray', linestyle='dashed')
                    ax.set_yscale("log")
                    ax.set_ylim(10,5*10**5)
                    plt.xticks(rotation=incline)
                    plt.ylabel('NEGATIVE Result forcasted [EUR]')
                    
                    # Display the bar chart in Streamlit
                    st.pyplot(fig)
                    
                with col4:
                    # Create a pie chart
                    conditions = (filter_df['PR_4casted'] < 0)
                    df_plot = filter_df[conditions].nsmallest(10,'PR_4casted').sort_values(by=['PR_4casted'])
                    fig, ax = plt.subplots()
                    ax.set_title('Master projects | NEGATIVE Result forcasted')
                    ax.pie(-df_plot['PR_4casted'], labels=df_plot['WO'], autopct='%1.f%%', startangle=90)
                    ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
                    
                    # Display the pie chart in Streamlit
                    st.pyplot(fig)
  
    

# =============================================================================
# 
# Streaming now
# 
# =============================================================================
trial = streaming()


