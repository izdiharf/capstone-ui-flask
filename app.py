from flask import Flask, render_template
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt

app = Flask(__name__)

playstore = pd.read_csv('data/googleplaystore.csv')

playstore.drop_duplicates(['App'], keep='first', inplace=True) 

# bagian ini untuk menghapus row 10472 karena nilai data tersebut tidak tersimpan pada kolom yang benar
playstore.drop([10472], inplace=True)

playstore.Category = playstore['Category'].astype('category')

playstore.Installs = playstore['Installs'].apply(lambda x: x.replace(',',''))
playstore.Installs = playstore['Installs'].apply(lambda x: x.replace('+',''))

# Bagian ini untuk merapikan kolom Size, Anda tidak perlu mengubah apapun di bagian ini
playstore['Size'].replace('Varies with device', np.nan, inplace = True ) 
playstore.Size = (playstore.Size.replace(r'[kM]+$', '', regex=True).astype(float) * \
             playstore.Size.str.extract(r'[\d\.]+([kM]+)', expand=False)
            .fillna(1)
            .replace(['k','M'], [10**3, 10**6]).astype(int))
playstore['Size'].fillna(playstore.groupby('Category')['Size'].transform('mean'),inplace = True)

playstore.Price = playstore['Price'].apply(lambda x: x.replace('$',''))
playstore.Price = playstore['Price'].astype('float64')

# Ubah tipe data Reviews, Size, Installs ke dalam tipe data integer
playstore[['Reviews', 'Size', 'Installs']] = playstore[['Reviews', 'Size', 'Installs']].astype('int64')

@app.route("/")
# This fuction for rendering the table
def index():
    df2 = playstore.copy()

    # Statistik
    top_category = pd.crosstab(
                  index=df2['Category'],
                  columns='Jumlah', 
                  values=df2['App'],
                  aggfunc='count'
                  ).sort_values(by='Jumlah', ascending=False)
    top_category.reset_index(inplace=True)
    top_category.head()

    # Dictionary stats digunakan untuk menyimpan beberapa data yang digunakan untuk menampilkan nilai di value box dan tabel
    stats = {
        'most_categories' : top_category['Category'][0],
        'total': top_category['Jumlah'][0],
        'rev_table' : df2.groupby(['Category', 'App']).agg({'Reviews': 'sum', 'Rating': 'mean'}).sort_values('Reviews', ascending=False).head(10).reset_index().to_html(classes=['table thead-light table-striped table-bordered table-hover table-sm'])
        }

    ## Bar Plot
    cat_order = top_category.groupby('Category').agg({
    'Jumlah' : 'sum'
    }).rename({'Category':'Total'}, axis=1).sort_values('Jumlah', ascending=False).head()
    X = cat_order['Jumlah'].keys()
    Y = cat_order['Jumlah']
    my_colors = 'rgbkymc'
    # bagian ini digunakan untuk membuat kanvas/figure
    fig = plt.figure(figsize=(8,3),dpi=300)
    fig.add_subplot()
    # bagian ini digunakan untuk membuat bar plot
    plt.barh(X,Y, color=my_colors)
    # bagian ini digunakan untuk menyimpan plot dalam format image.png
    plt.savefig('static/cat_order.png',bbox_inches="tight") 
    
    ## Scatter Plot
    X = df2['Reviews'].values # axis x
    Y = df2['Rating'].values # axis y
    area = playstore['Installs'].values/10000000 # ukuran besar/kecilnya lingkaran scatter plot
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    # isi nama method untuk scatter plot, variabel x, dan variabel y
    plt.scatter(x=X,y=Y, s=area, alpha=0.3)
    plt.xlabel('Reviews')
    plt.ylabel('Rating')
    plt.savefig('static/rev_rat.png',bbox_inches="tight")

    ## Histogram Size Distribution
    X=(df2['Size']/1000000).values
    fig = plt.figure(figsize=(5,5))
    fig.add_subplot()
    plt.hist(X,bins=100, density=True,  alpha=0.75)
    plt.xlabel('Size')
    plt.ylabel('Frequency')
    plt.savefig('static/hist_size.png',bbox_inches="tight")

    ## Buatlah sebuah plot yang menampilkan insight di dalam data 
    new_plot = df2.groupby('Genres').sum().sort_values('Reviews', ascending=False).head(10).plot.bar()
    plt.xlabel('Genres')
    plt.ylabel('Total')
    plt.savefig('static/new_plot.png',bbox_inches="tight")

    # Tambahkan hasil result plot pada fungsi render_template()
    return render_template('index.html', stats=stats)

if __name__ == "__main__":
    app.run(debug=True)
