import { Component, ElementRef, ViewChild, AfterViewChecked } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { ApiService } from '../../services/api.service';
import { TranslationService } from '../../services/translation.service';

interface Message {
  role: 'user' | 'bot';
  text: string;
  time: string;
  loading?: boolean;
  tag?: 'summary' | 'file';
}

@Component({
  selector: 'app-chatbot',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './chatbot.component.html',
  styleUrls: ['./chatbot.component.scss']
})
export class ChatbotComponent implements AfterViewChecked {
  @ViewChild('messagesEnd') messagesEnd!: ElementRef;
  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;

  open = false;
  question = '';
  loading = false;
  uploadingFile = false;
  summarizing = false;

  messages: Message[] = [
    {
      role: 'bot',
      text: "Hello! I'm your **Sougui data assistant**.\n\nAsk me anything about your sales, products, customers, or trends.\n\nType **help** to see what I can do.",
      time: this.now()
    }
  ];

  suggestions = [
    'Database summary',
    'Top 5 products',
    'Top customers',
    'Sales by category',
    'Monthly trend 2023',
    'Discount analysis',
    'Recent claims'
  ];

  constructor(
    private api: ApiService,
    public translate: TranslationService
  ) {}

  ngAfterViewChecked() { this.scrollToBottom(); }

  toggle() { this.open = !this.open; }

  ask(text?: string) {
    const q = (text || this.question).trim();
    if (!q || this.loading) return;

    this.messages.push({ role: 'user', text: q, time: this.now() });
    this.question = '';
    this.loading = true;

    const loadingMsg: Message = { role: 'bot', text: '', time: this.now(), loading: true };
    this.messages.push(loadingMsg);

    this.api.chatbotAsk(q).subscribe({
      next: (res) => {
        const idx = this.messages.indexOf(loadingMsg);
        if (idx !== -1) this.messages[idx] = { role: 'bot', text: res.answer || 'No response.', time: this.now() };
        this.loading = false;
      },
      error: () => {
        const idx = this.messages.indexOf(loadingMsg);
        if (idx !== -1) this.messages[idx] = {
          role: 'bot',
          text: 'Sorry, I could not connect to the database. Please make sure the backend is running.',
          time: this.now()
        };
        this.loading = false;
      }
    });
  }

  summarizeDB() {
    if (this.summarizing || this.loading) return;
    this.summarizing = true;

    this.messages.push({ role: 'user', text: '✨ Summarize database', time: this.now() });
    const loadingMsg: Message = { role: 'bot', text: '', time: this.now(), loading: true };
    this.messages.push(loadingMsg);

    this.api.chatbotSummarize().subscribe({
      next: (res) => {
        const idx = this.messages.indexOf(loadingMsg);
        if (idx !== -1) this.messages[idx] = { role: 'bot', text: res.answer, time: this.now(), tag: 'summary' };
        this.summarizing = false;
      },
      error: () => {
        const idx = this.messages.indexOf(loadingMsg);
        if (idx !== -1) this.messages[idx] = { role: 'bot', text: 'Could not generate summary. Check backend connection.', time: this.now() };
        this.summarizing = false;
      }
    });
  }

  triggerFileUpload() { this.fileInput?.nativeElement.click(); }

  onFileSelected(event: Event) {
    const input = event.target as HTMLInputElement;
    const file = input.files?.[0];
    if (!file) return;

    const ext = file.name.split('.').pop()?.toLowerCase();
    if (!['csv', 'pdf', 'xlsx', 'xls'].includes(ext || '')) {
      this.messages.push({ role: 'bot', text: '⚠️ Only **CSV**, **Excel** (.xlsx/.xls), and **PDF** files are supported.', time: this.now() });
      return;
    }

    this.uploadingFile = true;
    this.messages.push({ role: 'user', text: `📎 Uploaded: **${file.name}**`, time: this.now() });
    const loadingMsg: Message = { role: 'bot', text: '', time: this.now(), loading: true };
    this.messages.push(loadingMsg);

    const formData = new FormData();
    formData.append('file', file);

    this.api.chatbotUpload(formData).subscribe({
      next: (res) => {
        const idx = this.messages.indexOf(loadingMsg);
        if (idx !== -1) this.messages[idx] = { role: 'bot', text: res.answer, time: this.now(), tag: 'file' };
        this.uploadingFile = false;
      },
      error: (err) => {
        const idx = this.messages.indexOf(loadingMsg);
        if (idx !== -1) this.messages[idx] = {
          role: 'bot',
          text: `Could not process file: ${err.error?.error || 'Unknown error'}`,
          time: this.now()
        };
        this.uploadingFile = false;
      }
    });

    input.value = '';
  }

  onKey(event: KeyboardEvent) {
    if (event.key === 'Enter' && !event.shiftKey) { event.preventDefault(); this.ask(); }
  }

  clearChat() {
    this.messages = [{ role: 'bot', text: "Chat cleared. Ask me anything about your database!", time: this.now() }];
  }

  formatText(text: string): string {
    return text
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\n/g, '<br>');
  }

  get isBusy(): boolean { return this.loading || this.uploadingFile || this.summarizing; }

  private scrollToBottom() {
    try { this.messagesEnd?.nativeElement.scrollIntoView({ behavior: 'smooth' }); } catch {}
  }

  private now(): string {
    return new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  }
}
