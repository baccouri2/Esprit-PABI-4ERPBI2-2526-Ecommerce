import { Component, Input, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';

export interface Advice {
  type: 'success' | 'warning' | 'info' | 'danger';
  title: string;
  message: string;
  actions?: string[];
}

@Component({
  selector: 'app-advice-popup',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './advice-popup.component.html',
  styleUrls: ['./advice-popup.component.scss']
})
export class AdvicePopupComponent {
  @Input() advice: Advice | null = null;
  @Output() closed = new EventEmitter<void>();

  close() {
    this.closed.emit();
  }
}
