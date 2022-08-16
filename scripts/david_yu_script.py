import pandas as pd
import numpy as np
import geopandas as gpd

def crop():
    crop = pd.read_csv('./inputs/crop.csv')
    crop = crop[['field_id', 'field_geometry', 'crop_type']][crop['year'] == 2021]
    return crop.to_csv('./outputs/crop.csv')

def spec():
    sp = pd.read_csv('./inputs/spectral.csv')
    sp['year'] = pd.to_datetime(sp['date']).dt.year
    sp = sp[sp['year'] == 2021]
    def NDVI(a,b):
        return (a-b)/(a+b)
    sp['pos'] = sp.apply(lambda x: NDVI(x.nir, x.red), axis = 1)
    sp['pos_date'] = sp['date']
    return sp[['tile_id','tile_geometry','pos','pos_date']].to_csv('./outputs/spectral.csv')

def weighted_avg():
    soil = pd.read_csv('./inputs/soil.csv')
    soil['hzweights'] = abs(soil['hzdept'] - soil['hzdepb']) / soil['hzdept']
    soil['compweighted'] = soil['comppct'] * soil['hzweights'] / 100
    soil['compweighted'].replace([np.inf, -np.inf], 0, inplace=True)
    weighted_avg_comp = soil.groupby(['mukey'])['compweighted'].mean().reset_index()
    return weighted_avg_comp[['mukey', 'compweighted']].to_csv('./outputs/soil_avg.csv')

def soil():
    soil = pd.read_csv('./inputs/soil.csv')
    soil['hzweights'] = abs(soil['hzdept'] - soil['hzdepb']) / soil['hzdept']
    soil['compweighted'] = soil['comppct'] * soil['hzweights'] / 100
    return soil[['mukey', 'mukey_geometry', 'om', 'cec', 'ph']].to_csv('./outputs/soil.csv')

def weather():
    w = pd.read_csv('./inputs/weather.csv')
    w = w[w['year'] == 2021]
    crop = pd.read_csv('./inputs/crop.csv')
    crop_geo = crop[['field_id', 'field_geometry']]
    cropgdf = gpd.GeoDataFrame(
    crop_geo.loc[:, [c for c in crop_geo.columns if c != "geometry"]],
    gdf = gpd.GeoDataFrame(
        crop_geo.loc[:, [c for c in crop_geo.columns if c != "geometry"]],
        geometry=gpd.GeoSeries.from_wkt(crop_geo["geometry"]),
        crs="epsg:4326",
    )
    gdf['lon'] = gdf.centroid.map(lambda p: round(p.x, 2))
    gdf['lat'] = gdf.centroid.map(lambda p: round(p.y, 2))
    def state_county(lat, lon):
        url = 'https://geo.fcc.gov/api/census/block/find?latitude=%s&longitude=%s&format=json' % (lat, lon)
        response = requests.get(url)
        data = response.json()
        state = data['State']['FIPS']
        county = data['County']['FIPS'][2:]
        return state + county
    gdf['fips_code'] = gdf.apply(lambda x: state_county(x.lat, x.lon), axis = 1)
    gdf['fips_code'] = gdf['fips_code'].astype(int)
    w_geo = w.merge(gdf, how='left', left_on='fips_code', right_on='fips_code')
    final_w_geo_precip = w_geo.groupby('field_id')['precip'].sum()
    final_w_geo_min_temp = w_geo.groupby('field_id')['temp'].min()
    final_w_geo_max_temp = w_geo.groupby('field_id')['temp'].max()
    final_w_geo_mean_temp = w_geo.groupby('field_id')['temp'].mean()
    final_w_geo = pd.DataFrame({'field_id': final_w_geo_precip.index,
                                'precip': final_w_geo_precip,
                                'min_temp': final_w_geo_min_temp,
                                'max_temp': final_w_geo_max_temp,
                                'mean_temp': final_w_geo_mean_temp
                            })
    return final_w_geo.to_csv('./outputs/weather.csv')

def main():
    crop()
    spec()
    weighted_avg()
    soil()
    weather()

if __name__ == "__main__":
 main()