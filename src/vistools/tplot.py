from numpy import flip
import plotly.graph_objects as go


def plot_3d(ds_raster, plotpath):
    height_band = ds_raster.read(1)
    w, h = height_band.shape
    resolution = ds_raster.res[0]
    offset = 200
    trimmed_ds = flip(height_band[int(w/2-offset):int(w/2+offset),
                                  int(h/2-offset):int(h/2+offset)], 1)

    fig = go.Figure(
        data=[go.Surface(z=trimmed_ds, colorscale='Fall',
                         hovertemplate='<b>Height:</b> %{z:.0f} m<extra></extra>',
                         lightposition=dict(x=100,
                                            y=100,
                                            z=2000),)], )
    fig.update_layout(autosize=True,
                      margin=dict(l=65, r=50, b=65, t=90),
                      scene_camera=dict(
                          eye=dict(x=0.75, y=0.5, z=0.005),
                      ),
                      template='plotly_white',
                      scene=dict(
                          xaxis=dict(visible=False, showgrid=False,
                                     zeroline=False),
                          yaxis=dict(visible=False, showgrid=False,
                                     zeroline=False),
                          zaxis=dict(visible=False, showgrid=False),
                          aspectmode='manual',
                          aspectratio=dict(x=1, y=1, z=1.5/resolution),


                      ),

                      showlegend=False,
                      )
    fig.update_traces(showlegend=False)
    fig.write_json(plotpath)
