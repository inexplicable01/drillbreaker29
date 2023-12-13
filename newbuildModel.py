import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error
from sklearn.preprocessing import StandardScaler, OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from joblib import dump
# Load data
df = pd.read_csv('newbuild2016.csv')
# List of columns to ignore
ignore_columns = [  'comments', 'point_x', 'point_y', 'sitetype','home_type','shape_length','newbuild_prediction']

# Drop the target variable and the columns to ignore from the features
X = df.drop(['zestimate_value'] + ignore_columns, axis=1)

# Preprocess and split data
y = df['zestimate_value']  # Target variable

# Define categorical and numerical features
categorical_features = X.select_dtypes(include=['object']).columns
numerical_features = X.select_dtypes(include=['int64', 'float64']).columns

# Preprocessing for numerical data
numerical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='median')),
    ('scaler', StandardScaler())])

# Preprocessing for categorical data
categorical_transformer = Pipeline(steps=[
    ('imputer', SimpleImputer(strategy='most_frequent')),
    ('onehot', OneHotEncoder(handle_unknown='ignore'))])

# Bundle preprocessing for numerical and categorical data
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numerical_transformer, numerical_features),
        ('cat', categorical_transformer, categorical_features)])

# Create a preprocessing and modelling pipeline
model = Pipeline(steps=[('preprocessor', preprocessor),
                        ('model', LinearRegression())])

# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=0)

# Train the model
model.fit(X_train, y_train)

# Predict and evaluate
y_pred = model.predict(X_test)
print(f'Mean Squared Error: {mean_squared_error(y_test, y_pred)}')

for i, value in enumerate(y_test):

    # if X_test['haswaterfrontview'].iloc[i]==1:
    print(y_test.iloc[i], round(y_pred[i]),round(y_test.iloc[i]- y_pred[i]), X_test['addr_full'].iloc[i] , X_test['id'].iloc[i])


# Save the model to a file
model_filename = 'linear_regression_model.joblib'
dump(model, model_filename)
print(f"Model saved to {model_filename}")