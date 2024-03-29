query = session.query(BellevueTaxAddress).filter(BellevueTaxAddress.year_built > 2016)
df = pd.read_sql(query.statement, session.bind)
csv_file_name = 'newbuild2016.csv'
df.to_csv(csv_file_name, index=False)
print_and_log(f"Data written to {csv_file_name}")