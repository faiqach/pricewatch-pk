import 'package:flutter/material.dart';

import '../utils/colors.dart';

class CropPriceTile extends StatelessWidget {
  final String emoji;
  final String name;
  final double price;
  final double? previousPrice;
  final String unit;
  final String trend;
  final double percentChange;
  final double? vendorPrice;

  const CropPriceTile({
    super.key,
    required this.emoji,
    required this.name,
    required this.price,
    required this.unit,
    required this.trend,
    required this.percentChange,
    this.previousPrice,
    this.vendorPrice,
  });

  @override
  Widget build(BuildContext context) {
    final Color trendColor;
    final IconData trendIcon;
    final String trendIndicator;

    switch (trend) {
      case 'up':
        trendColor = Colors.green.shade600;
        trendIcon = Icons.arrow_upward_rounded;
        trendIndicator = '🟢';
        break;
      case 'down':
        trendColor = Colors.red.shade600;
        trendIcon = Icons.arrow_downward_rounded;
        trendIndicator = '🔴';
        break;
      default:
        trendColor = Colors.amber.shade700;
        trendIcon = Icons.remove_rounded;
        trendIndicator = '⚪';
    }

    final double prevP = previousPrice ?? price;
    final double? deviationPercent =
        (vendorPrice != null && price != 0) ? ((vendorPrice! - price) / price * 100) : null;
    final bool isOverpriced = deviationPercent != null && deviationPercent >= 15;

    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.05),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Row(
        children: [
          Text(emoji, style: const TextStyle(fontSize: 28)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  name,
                  style: const TextStyle(
                    color: kTextDark,
                    fontSize: 14,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                const SizedBox(height: 2),
                Row(
                  children: [
                    Text(
                      '$trendIndicator Old: ${prevP.toStringAsFixed(0)}',
                      style: TextStyle(
                        color: kTextLight,
                        fontSize: 11,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const Text(' → ', style: TextStyle(color: kTextLight, fontSize: 11)),
                    Text(
                      'New: ${price.toStringAsFixed(0)}',
                      style: TextStyle(
                        color: trendColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                  ],
                ),
                if (deviationPercent != null && vendorPrice != price) ...[
                  const SizedBox(height: 3),
                  Row(
                    children: [
                      Text(
                        'Vendor: ${vendorPrice!.toStringAsFixed(0)} '
                        '(${deviationPercent >= 0 ? '+' : ''}${deviationPercent.toStringAsFixed(1)}%)',
                        style: TextStyle(
                          color: isOverpriced ? Colors.red.shade700 : kTextLight,
                          fontSize: 10.5,
                          fontWeight: isOverpriced ? FontWeight.w700 : FontWeight.w500,
                        ),
                      ),
                      if (isOverpriced) ...[
                        const SizedBox(width: 5),
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 5, vertical: 1),
                          decoration: BoxDecoration(
                            color: Colors.red.shade50,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: Colors.red.shade200),
                          ),
                          child: Text(
                            'Overpriced',
                            style: TextStyle(
                              color: Colors.red.shade700,
                              fontSize: 9,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ],
            ),
          ),
          Column(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text(
                'PKR ${price.toStringAsFixed(0)}',
                style: const TextStyle(
                  color: kPrimaryColor,
                  fontSize: 15,
                  fontWeight: FontWeight.w800,
                ),
              ),
              const SizedBox(height: 2),
              Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Icon(trendIcon, color: trendColor, size: 14),
                  const SizedBox(width: 2),
                  Text(
                    trend == 'stable'
                        ? '0.0%'
                        : '${trend == 'up' ? '+' : '-'}${percentChange.toStringAsFixed(1)}%',
                    style: TextStyle(
                      color: trendColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ),
            ],
          ),
        ],
      ),
    );
  }
}
