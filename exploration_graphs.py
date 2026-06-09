from fredapi import Fred
import os
from dotenv import load_dotenv
import matplotlib.pyplot as plt

load_dotenv()

fred = Fred(api_key = os.getenv('FRED_API_KEY'))

fed_funds = fred.get_series('FEDFUNDS', observation_starts = '2010-01-01')

aerospace_ppi = fred.get_series('PCU336411336411', observation_start='2010-01-01')

defense = fred.get_series('FDEFX', observation_start='2010-01-01')

fig, axes = plt.subplots(3, 1, figsize = (12, 10))

axes[0].plot(fed_funds.index, fed_funds.values)
axes[0].set_title('Federal Funds Rate')
axes[0].set_ylabel('%')

axes[1].plot(aerospace_ppi.index, aerospace_ppi.values)
axes[1].set_title('Aerospace PPI')

axes[2].plot(defense.index, defense.values)
axes[2].set_title('Defense Spending')

plt.tight_layout()
plt.show()
