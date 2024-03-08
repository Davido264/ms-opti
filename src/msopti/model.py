# import typing
# import lightgbm as lgb
# import mlforecast
# from mlforecast import forecast
# import numpy as np
# import pandas as pd
# import os
# from mlforecast import target_transforms, lag_transforms
# from matplotlib import pyplot as plt
# from utilsforecast.plotting import plot_series
# import neuralforecast
# from neuralforecast import models as neuralmodels
# import prophet
# from prophet import serialize as pser
# 
# 
# def train_ml_model(force_retrain: bool = True) -> mlforecast.MLForecast:
#     if os.path.exists(os.path.join(os.environ["MODEL_PATH"],"model.pkt")) and not force_retrain:
#         return mlforecast.MLForecast.load(os.environ["MODEL_PATH"])
# 
#     df = pd.read_csv(os.environ["DATASET_PATH"])
#     train_df = pd.DataFrame()
# 
#     train_df["ds"] = pd.to_datetime(df["timespan"],format="%Y-%m-%d %H:%M:%S")
#     train_df["unique_id"] = df["stop_id"]
#     train_df["y"] = df["passengers"]
# 
#     models = {
#         "avg": lgb.LGBMRegressor(num_leaves=512,n_estimators=50),
#         "q75": lgb.LGBMRegressor(num_leaves=512,n_estimators=50, objective="quantile", alpha=0.75),
#         "q25": lgb.LGBMRegressor(num_leaves=512,n_estimators=50, objective="quantile", alpha=0.25),
#     }
# 
#     lt = {
#         1: [lag_transforms.ExpandingMean()],
#         12: [lag_transforms.RollingMean(window_size=24)],
#     }
# 
#     model = mlforecast.MLForecast(
#         models = typing.cast(forecast.Models,models),
#         freq="5min",
#         target_transforms=[target_transforms.Differences([12])],
#         lags=[1, 12],
#         lag_transforms = lt,
#     )
# 
#     model.fit(train_df)
#     model.save(os.environ["MODEL_PATH"])
#     return model
# 
# def train_neural_model(force_retrain: bool = True) -> neuralforecast.NeuralForecast:
#     if os.path.exists(os.path.join(os.environ["MODEL_PATH"],"model.pkt")) and not force_retrain:
#         return neuralforecast.NeuralForecast.load(os.environ["MODEL_PATH"])
# 
#     df = pd.read_csv(os.environ["DATASET_PATH"])
#     train_df = pd.DataFrame()
# 
#     train_df["ds"] = pd.to_datetime(df["timespan"],format="%Y-%m-%d %H:%M:%S")
#     train_df["unique_id"] = df["stop_id"]
#     train_df["y"] = df["passengers"]
#     test = typing.cast(pd.DataFrame,train_df[train_df["ds"] > "2024-03-23"])
#     train_df = typing.cast(pd.DataFrame,train_df[train_df["ds"] <= "2024-03-23"])
# 
#     horizon = len(test)
#     print(test)
# 
#     models = [
#         neuralmodels.NBEATS(input_size=5 * horizon, h=horizon, max_steps=50, start_padding_enabled=True),
#         neuralmodels.NHITS(input_size=5 * horizon, h=horizon, max_steps=50, start_padding_enabled=True)
#     ]
# 
#     model = neuralforecast.NeuralForecast(
#         models = models,
#         freq = "5min",
#     )
# 
#     model.fit(train_df)
#     model.save(os.environ["MODEL_PATH"])
#     return model
# 
# def train_prophet(force_retrain: bool) -> prophet.Prophet:
#     path = os.path.join(os.environ["MODEL_PATH"],"serialized_model.json")
#     if os.path.exists(path) and not force_retrain:
#         with open(path , 'r') as fin:
#             m = pser.model_from_json(fin.read())
#         return m
# 
#     df = pd.read_csv(os.environ["DATASET_PATH"])
#     train_df = pd.DataFrame()
# 
#     train_df["ds"] = pd.to_datetime(df["timespan"],format="%Y-%m-%d %H:%M:%S")
#     train_df["y"] = df["passengers"]
#     train_df["unique_id"] = df["stop_id"]
#     train_df = train_df[train_df["unique_id"] == 0]
#     train_df.drop(["unique_id"],inplace=True,axis=1)
#     test = typing.cast(pd.DataFrame,train_df[train_df["ds"] > "2024-03-23"])
#     train_df = typing.cast(pd.DataFrame,train_df[train_df["ds"] <= "2024-03-23"])
# 
#     m = prophet.Prophet(growth="linear", seasonality_mode="multiplicative")
#     m.fit(train_df)
#     with open(path, 'w') as fout:
#         fout.write(pser.model_to_json(m))  # Save model
# 
#     return m
# 
# 
# def test_prophet():
#     df = pd.read_csv(os.environ["DATASET_PATH"])
# 
#     train_df = pd.DataFrame()
# 
#     train_df["ds"] = pd.to_datetime(df["timespan"],format="%Y-%m-%d %H:%M:%S")
#     train_df["y"] = df["passengers"]
#     train_df["unique_id"] = df["stop_id"]
#     train_df = train_df[train_df["unique_id"] == 0]
#     train_df.drop(["unique_id"],inplace=True,axis=1)
#     test = typing.cast(pd.DataFrame,train_df[train_df["ds"] > "2024-03-23"])
#     train_df = typing.cast(pd.DataFrame,train_df[train_df["ds"] <= "2024-03-23"])
# 
#     with open(os.path.join(os.environ["MODEL_PATH"],"serialized_model.json") , 'r') as fin:
#         m = pser.model_from_json(fin.read())
# 
#     preds = pd.merge(
#         test,
#         m.predict(test),
#         on="ds",
#         how="inner"
#     )
# 
#     mape = ((preds["yhat"] - preds["y"]).abs() / preds["y"]).mean()
#     print(mape)
#     fig1 = m.plot_components(preds)
#     # fig1.show()
#     fig2, ax = plt.subplots(figsize=(11, 5))
#     ax.scatter(preds["ds"], preds["y"], color="black", marker=".")
#     ax.plot(preds["ds"], preds["yhat"], label=f"linear, mape={mape:.1%}")
#     ax.plot(test["ds"], test["y"], label="true")
#     plt.xticks(rotation=60)
#     ax.legend()
#     plt.show(block=True)
# 
# 
# def test_model(model: mlforecast.MLForecast):
#     df = pd.read_csv(os.environ["DATASET_TEST_PATH"])
#     # df = df[(df["stop_id"] == 0)]
# 
#     # pred = model.predict(12 * 24 * 7 * 4)
#     # pred = pred[(pred["unique_id"] == 0)]
#     # pred["ds"] = pred["ds"].map(lambda x: str(x))
# 
#     train_df = pd.DataFrame()
# 
#     train_df["ds"] = pd.to_datetime(df["timespan"],format="%Y-%m-%d %H:%M:%S")
#     train_df["unique_id"] = df["stop_id"]
#     train_df["y"] = df["passengers"]
# 
#     # val = model.cross_validation(
#     #     train_df,
#     #     n_windows=4,  # number of models to train/splits to perform
#     #     h=24,  # length of the validation set in each window
#     # )
# 
#     fig = plot_series(train_df, model.predict(12 * 24 * 7 * 4), max_insample_length= 12 * 24 * 7 * 4)
#     # plt.plot(df["timespan"],df["passengers"])
#     # plt.plot(pred["ds"],pred["avg"])
#     # plt.plot(pred["ds"],pred["q25"])
#     # plt.plot(pred["ds"],pred["q75"])
#     # plt.legend()
#     fig.show()
# 
# def test_neural_model(nf: neuralforecast.NeuralForecast):
#     df = pd.read_csv(os.environ["DATASET_PATH"])
#     train_df = pd.DataFrame()
# 
#     train_df["ds"] = pd.to_datetime(df["timespan"],format="%Y-%m-%d %H:%M:%S")
#     train_df["unique_id"] = df["stop_id"]
#     train_df["y"] = df["passengers"]
#     test = typing.cast(pd.DataFrame,train_df[train_df["ds"] > "2024-03-23"])
#     train_df = typing.cast(pd.DataFrame,train_df[train_df["ds"] <= "2024-03-23"])
# 
#     y_hat = nf.predict().reset_index()
#     fig, ax = plt.subplots(1, 1, figsize = (20, 7))
#     y_hat = test.merge(y_hat, how='left', on=['unique_id', 'ds'])
#     plot_df = pd.concat([df, y_hat]).set_index('ds')
# 
#     plot_df[['y', 'NBEATS', 'NHITS']].plot(ax=ax, linewidth=2)
# 
#     ax.set_title('AirPassengers Forecast', fontsize=22)
#     ax.set_ylabel('Monthly Passengers', fontsize=20)
#     ax.set_xlabel('Timestamp [t]', fontsize=20)
#     ax.legend(prop={'size': 15})
#     ax.grid()
# 
# 
# 
# if __name__ == "__main__":
#     model = train_prophet(force_retrain=True)
#     test_prophet()
