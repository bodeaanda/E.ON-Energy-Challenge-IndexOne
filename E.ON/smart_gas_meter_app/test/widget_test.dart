import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:smart_gas_meter_app/main.dart';

void main() {
  testWidgets('Verifies if the app is starting', (WidgetTester tester) async {
    await tester.pumpWidget(const MyApp());
    expect(find.text('Istoric Consum Gaz'), findsOneWidget);
  });
}