export default function ProfitBox({ profit, roi }) {
  if (profit == null) return null
  const positive = profit > 0
  return (
    <div className={`rounded border p-3 text-center ${positive ? 'border-profit-green/40 bg-profit-green/5' : 'border-crimson/40 bg-crimson/5'}`}>
      <div className={`text-lg font-bold ${positive ? 'text-profit-green' : 'text-crimson'}`}>
        {positive ? '+' : ''}{profit.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}
      </div>
      {roi != null && (
        <div className="text-xs text-bone/50 mt-0.5">ROI: {roi.toFixed(1)}%</div>
      )}
    </div>
  )
}
